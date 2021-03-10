from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext

from database import schemas
from src.runner import dp
from src.database import crud
from src.database.entities import Subscriber
from src.services.social.broadcasters import vk_broadcaster

from .states import UserSettings
from .markups.user import (
    actions_cb,
    main_menu_kb,
    user_settings_kb,
    back_to_main_menu_kb,
    get_logs_settings_kb,
)


@dp.message_handler(text="Настройки", state="*")
async def user_settings_menu(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await message.answer(
        "Ты находишься в меню настроек бота, "
        "здесь можно установить лог-канал а так же изменить способ ввода стен",
        reply_markup=user_settings_kb,
    )


@dp.message_handler(text="FAQ")
async def user_faq(message: Message):
    await message.answer("FAQ")


@dp.callback_query_handler(actions_cb.filter(action=["logs_channel", "change_mode"]))
async def cb_user_change_settings(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    log_channel = await crud.target.get_log_channel(subscriber.id)
    if action == "logs_channel":
        if log_channel:
            channel_log_link = await dp.bot.export_chat_invite_link(log_channel.source_id)
            logs_active = await vk_broadcaster.is_user_logs_active(query.from_user.id)
            alias = {True: "логирование включено", False: "логирование отключено"}
            logs_settings_kb = get_logs_settings_kb(logs_active)
            await query.message.edit_text(
                f"Ссылка на канал с логами {channel_log_link}\n{alias[logs_active]}",
                reply_markup=logs_settings_kb,
            )
        else:
            await UserSettings.set_log_channel.set()
            await query.message.edit_text(
                "Лог канал нужен, чтобы отслеживать состояние всех ваших стен\nВведи telegram_id, чтобы привязать канал"
                "Чтобы узнать свой или id группы, воспользуйся @myidbot @getmyid_bot",
                reply_markup=back_to_main_menu_kb,
            )
    if action == "change_mode":
        await query.message.edit_text("Режим ввода: стандартный", reply_markup=back_to_main_menu_kb)


@dp.message_handler(state=UserSettings.set_log_channel)
async def fsm_user_set_log_channel(message: Message, subscriber: Subscriber, state: FSMContext):
    channel_id, error = await UserSettings.get_log_channel(message.text)

    if error:
        return await message.reply(f"Ошибка\n\n{error}\n\nПопробуй снова", reply_markup=back_to_main_menu_kb)

    await crud.target.add_source(
        schemas.ForwardCreate(
            target_id=subscriber.id,
            source_id=channel_id,
            source_type="logs",
            source_short_name="None",
            sleep=0,
            to_chat_id=channel_id,
            fetch_count=0,
        )
    )

    await vk_broadcaster.update_log_channel(message.from_user.id, channel_id)
    await state.finish()
    await message.answer("Успешно", reply_markup=user_settings_kb)


@dp.callback_query_handler(actions_cb.filter(action=["disable_logs", "enable_logs", "remove_logs"]))
async def cq_change_logs_settings(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    log_channel = await crud.target.get_log_channel(subscriber.id)
    channel_log_link = await dp.bot.export_chat_invite_link(log_channel.source_id)
    message_text = f"Ссылка на канал с логами {channel_log_link}"

    if action == "disable_logs":
        await vk_broadcaster.update_log_channel(query.from_user.id, log_channel.source_id, False)
        logs_settings_kb = get_logs_settings_kb(False)
        await query.message.edit_text(f"{message_text}\nлогирование отключено", reply_markup=logs_settings_kb)

    if action == "enable_logs":
        await vk_broadcaster.update_log_channel(query.from_user.id, log_channel.source_id, True)
        logs_settings_kb = get_logs_settings_kb(True)
        await query.message.edit_text(f"{message_text}\nлогирование включено", reply_markup=logs_settings_kb)

    if action == "remove_logs":
        await crud.target.remove_source_data(log_channel.source_id, subscriber.id)
        await vk_broadcaster.update_log_channel(query.from_user.id, -1, False)
        await query.message.edit_text(
            "Успешно, созданный лог-канал нужно удалить вручную", reply_markup=main_menu_kb
        )
