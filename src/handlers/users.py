from loguru import logger
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from src.runner import dp, vk_scheduler
from src.utils.keyboards import Constructor

from .states import UserVkData
from .markups.user import (
    user_cb,
    vk_wall_cb,
    main_user_menu,
    main_user_vk_menu,
    user_add_vk_walls,
    main_user_twitter_menu,
)

back_to_main_vk_btn = Constructor.create_inline_kb(
    [{"text": "Назад", "cb": ({"action": "main_vk"}, user_cb)}], [1]
)


@dp.message_handler(Command("service"))
async def cmd_user_services(message: Message):
    await message.answer("Выберите сервис", reply_markup=main_user_menu)


@dp.callback_query_handler(user_cb.filter(action="main"))
async def cq_user_main_services(query: CallbackQuery, callback_data: dict):
    logger.info(callback_data)
    await query.message.edit_text("Выберите сервис", reply_markup=main_user_menu)


@dp.callback_query_handler(user_cb.filter(action="main_vk"), state="*")
async def cq_user_vk_main(query: CallbackQuery, callback_data: dict, state: FSMContext):
    logger.info(f"cb: {callback_data}, state: {state}")
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await query.message.edit_text("ВКонтакте", reply_markup=main_user_vk_menu)


@dp.callback_query_handler(user_cb.filter(action=["add_vk", "status_vk"]))
async def cq_user_vk_actions(query: CallbackQuery, callback_data: dict):
    logger.info(callback_data)
    if callback_data["action"] == "status_vk":
        await query.message.edit_text(f"{vk_scheduler.is_running.get()}", reply_markup=back_to_main_vk_btn)
    elif callback_data["action"] == "add_vk":
        await query.message.edit_text(
            f"Доступные параметры опроса",
            reply_markup=user_add_vk_walls,
        )


@dp.callback_query_handler(vk_wall_cb.filter())
async def cq_user_add_vk_wall(query: CallbackQuery, callback_data: dict):
    logger.info(f"cb: {callback_data}")
    await UserVkData.add_wall_id.set()
    await query.answer("Введите wall_id", show_alert=True)


@dp.message_handler(
    lambda message: not UserVkData.is_wall_id_valid(message.text), state=UserVkData.add_wall_id
)
async def user_error_vk_wall_id_input(message: Message):
    return await message.reply(
        "Вы ввели ошибочный wall_id, попробуйте снова", reply_markup=back_to_main_vk_btn
    )


@dp.message_handler(state=UserVkData.add_wall_id)
async def user_add_vk_wall(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data["wall_id"] = message.text

    await UserVkData.next()
    await message.reply("Введите telegram_id")


@dp.message_handler(
    lambda message: not UserVkData.is_tg_id_valid(message.text), state=UserVkData.add_telegram_id
)
async def user_error_tg_id_input(message: Message):
    return await message.reply("Вы ввели ошибочный tg_id, попробуйте снова", reply_markup=back_to_main_vk_btn)


@dp.message_handler(state=UserVkData.add_telegram_id)
async def user_add_tg_id(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data["tg_id"] = message.text
    await state.finish()
    await message.answer("Успешно", reply_markup=main_user_vk_menu)


@dp.callback_query_handler(user_cb.filter(action="main_twitter"))
async def cq_user_twitter_main(query: CallbackQuery, callback_data: dict):
    logger.info(f"cb: {callback_data}")
    await query.message.edit_text("В разработке", reply_markup=main_user_twitter_menu)
