from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext

from src.runner import dp
from src.database import crud, schemas
from src.utils.keyboards import Constructor
from src.database.entities import Subscriber
from src.services.vk.public import vk_scheduler, vk_scheduler_cb

from .states import UserVkData
from .markups.user import (
    actions_cb,
    vk_wall_cb,
    main_menu_kb,
    vk_main_menu_kb,
    vk_fetch_count_cb,
    vk_wall_manage_cb,
    get_wall_manage_kb,
    twitter_main_menu_kb,
    vk_walls_timeouts_kb,
    back_to_vk_main_menu_kb,
    get_wall_fetch_count_kb,
)


@dp.callback_query_handler(actions_cb.filter(action="main"))
async def cq_user_main_services(query: CallbackQuery):
    await query.message.edit_text("Выберите сервис", reply_markup=main_menu_kb)


@dp.callback_query_handler(actions_cb.filter(action="vk_main"), state="*")
async def cq_user_vk_main(query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await query.message.edit_text("ВКонтакте", reply_markup=vk_main_menu_kb)


@dp.callback_query_handler(actions_cb.filter(action=["vk_status", "vk_view", "vk_add"]))
async def cq_user_vk_actions(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    walls_headers = await crud.forwarder.get(subscriber.id)
    walls = await crud.forwarder.get_sources_data(subscriber.id)

    if action == "vk_add":
        if len(walls) != walls_headers.max_count:
            await UserVkData.set_wall_id.set()
            await query.message.edit_text(
                f"{len(walls)}/{walls_headers.max_count}\nВведите wall_id",
                reply_markup=back_to_vk_main_menu_kb,
            )
        else:
            await query.message.edit_text(
                "Достигнуто максимальное кол-во стен для вашего уровня подписки.\n",
                reply_markup=back_to_vk_main_menu_kb,
            )

    if action == "vk_status":
        active_jobs = vk_scheduler.get_user_jobs(query.from_user.id)
        if active_jobs:
            await query.answer(f"Активных задач: {len(active_jobs)}", show_alert=True)
        else:
            await query.answer("У вас нет активных задач", show_alert=True)

    if action == "vk_view":
        if walls:
            walls_kb = Constructor.create_inline_kb(
                [
                    {
                        "text": wall.source_id,
                        "cb": ({"id": wall.source_id, "action": "wall_view"}, vk_wall_manage_cb),
                    }
                    for wall in walls
                ],
                [1] * len(walls),
            )
            walls_kb.add(back_to_vk_main_menu_kb.inline_keyboard[-1][0])
        else:
            walls_kb = back_to_vk_main_menu_kb
        await query.message.edit_text(
            f"Ваши стены\nЗанято {len(walls)} из {walls_headers.max_count} слотов\n"
            f"Выберите стену для управления её состоянием",
            reply_markup=walls_kb,
        )


@dp.message_handler(
    lambda message: not UserVkData.is_wall_id_valid(message.text), state=UserVkData.set_wall_id
)
async def fsm_user_error_vk_wall_id_input(message: Message):
    return await message.reply(
        "Вы ввели ошибочный wall_id, попробуйте снова", reply_markup=back_to_vk_main_menu_kb
    )


@dp.message_handler(state=UserVkData.set_wall_id)
async def fsm_user_add_vk_wall(message: Message, state: FSMContext):
    await UserVkData.next()
    await state.update_data({"wall_id": int(message.text)})
    await message.answer("Введите telegram_id", reply_markup=back_to_vk_main_menu_kb)


@dp.message_handler(
    lambda message: not UserVkData.is_telegram_id_valid(message.text), state=UserVkData.set_telegram_id
)
async def fsm_user_error_tg_id_input(message: Message):
    return await message.reply(
        "Вы ввели ошибочный telegram_id, попробуйте снова", reply_markup=back_to_vk_main_menu_kb
    )


@dp.message_handler(state=UserVkData.set_telegram_id)
async def fsm_user_add_telegram_id(message: Message, state: FSMContext):
    await UserVkData.next()
    await state.update_data({"tg_id": int(message.text)})
    await message.answer("Выберите период опроса стены", reply_markup=vk_walls_timeouts_kb)


@dp.callback_query_handler(vk_wall_cb.filter(), state=UserVkData.set_sleep)
async def fsm_user_set_vk_sleep(
    query: CallbackQuery, callback_data: dict, subscriber: Subscriber, state: FSMContext
):
    await UserVkData.next()
    await state.update_data({"sleep": callback_data["time"]})
    await query.message.edit_text(
        "Выберите количество постов которое, нужно получить со стены\n"
        f"Для вашего уровня подписки '{subscriber.level}' доступны следующие варианты\n"
        f"Default - 1 пост в заданный таймаут",
        reply_markup=get_wall_fetch_count_kb(subscriber.level),
    )


@dp.callback_query_handler(vk_fetch_count_cb.filter(), state=UserVkData.set_fetch_count)
async def fsm_user_set_fetch_count(
    query: CallbackQuery, callback_data: dict, subscriber: Subscriber, state: FSMContext
):
    fsm_store = await state.get_data()
    await crud.forwarder.add_source(
        schemas.WallSourceCreate(
            forwarder_target_id=subscriber.id,
            source_id=fsm_store["wall_id"],
            type="vkontakte",
            telegram_target_id=fsm_store["tg_id"],
            sleep=fsm_store["sleep"],
            fetch_count=callback_data["count"],
        )
    )
    await state.finish()
    await query.message.edit_text("Успешно!", reply_markup=vk_main_menu_kb)


@dp.callback_query_handler(vk_wall_manage_cb.filter())
async def cq_user_manage_vk_wall(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    wall_id = int(callback_data["id"])
    full_info = await crud.forwarder.get_source_data(wall_id, subscriber.id)

    if action == "wall_view":
        wall_manage_kb = get_wall_manage_kb(wall_id)
        await query.message.edit_text(
            f"Стена {full_info.source_id}\nвремя опроса: {full_info.sleep}, источник: {full_info.type}",
            reply_markup=wall_manage_kb,
        )

    if action == "wall_start":
        vk_scheduler.add_job(
            query.from_user.id, wall_id, full_info.telegram_target_id, full_info.sleep, full_info.fetch_count
        )
        await query.answer("Запущено")

    if action == "wall_remove":
        await crud.forwarder.remove_source_data(wall_id, subscriber.id)
        await vk_scheduler.remove_job(query.from_user.id, wall_id, full_info.telegram_target_id)
        await query.answer("Удалено", show_alert=True)

    if action == "wall_pause":
        vk_scheduler.pause_job(query.from_user.id, wall_id, full_info.telegram_target_id)
        await query.answer("Остановлено", show_alert=True)

    if action == "wall_resume":
        vk_scheduler.continue_job(query.from_user.id, wall_id, full_info.telegram_target_id)
        await query.answer("Восстановлено", show_alert=True)


@dp.callback_query_handler(vk_scheduler_cb.filter())
async def cq_vk_scheduler(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    wall_id = int(callback_data["id"])
    full_info = await crud.forwarder.get_source_data(wall_id, subscriber.id)
    if action == "auto":
        await vk_scheduler.update_delivery_settings(
            query.from_user.id, wall_id, full_info.telegram_target_id, "auto"
        )
        await query.message.edit_text("Авторепосты включены", reply_markup=back_to_vk_main_menu_kb)
    if action == "now":
        await vk_scheduler.update_delivery_settings(
            query.from_user.id, wall_id, full_info.telegram_target_id, "now"
        )
        await query.message.edit_text("Репостим", reply_markup=back_to_vk_main_menu_kb)
    if action == "timeout":
        await query.message.edit_text("Таймаут", reply_markup=back_to_vk_main_menu_kb)

    if action == "confirm":
        await query.message.edit_reply_markup(vk_main_menu_kb)


@dp.callback_query_handler(actions_cb.filter(action="twitter_main"))
async def cq_user_twitter_main(query: CallbackQuery):
    await query.message.edit_text("В разработке", reply_markup=twitter_main_menu_kb)
