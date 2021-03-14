from uuid import uuid4

from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold
from aiogram.utils.exceptions import BadRequest

from src.runner import dp
from src.database import crud, schemas
from src.utils.keyboards import Constructor
from src.database.entities import Subscriber
from src.services.social.broadcasters import vk_broadcaster

from .states import UserVkSettings
from .markups.user import (
    actions_cb,
    main_menu_kb,
    vk_main_menu_kb,
    vk_wall_manage_cb,
    vk_wall_params_cb,
    get_wall_manage_kb,
    get_wall_timeout_kb,
    twitter_main_menu_kb,
    back_to_vk_main_menu_kb,
    get_wall_fetch_count_kb,
)


@dp.callback_query_handler(actions_cb.filter(action="main"), state="*")
async def cq_user_main_services(query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await query.message.edit_text("Выбери сервис", reply_markup=main_menu_kb)


@dp.callback_query_handler(actions_cb.filter(action="vk_main"), state="*")
async def cq_user_vk_main(query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await query.message.edit_text("ВКонтакте", reply_markup=vk_main_menu_kb)


@dp.callback_query_handler(actions_cb.filter(action=["vk_status", "vk_view", "vk_add"]))
async def cq_user_vk_actions(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    walls_headers = await crud.target.get(subscriber.id)
    walls = await crud.target.get_sources_data(subscriber.id)

    if action == "vk_add":
        if len(walls) != walls_headers.max_count:
            await UserVkSettings.add_wall_id.set()
            await query.message.edit_text(
                f"Доступно {len(walls)}/{walls_headers.max_count} стен\n"
                f"Вставь ссылку на сообщество или стену\n"
                f"Например https://vk.com/durov или durov\nНа текущий момент "
                f"поддерживаются только открытые стены",
                reply_markup=back_to_vk_main_menu_kb,
            )
        else:
            await query.message.edit_text(
                "Достигнуто максимальное кол-во стен для вашего уровня подписки.\n",
                reply_markup=back_to_vk_main_menu_kb,
            )

    if action == "vk_status":
        active_jobs = vk_broadcaster.get_user_jobs(query.from_user.id)
        if active_jobs:
            await query.answer(f"Активных задач: {len(active_jobs)}", show_alert=True)
        else:
            await query.answer("У вас нет активных задач", show_alert=True)

    if action == "vk_view":
        if walls:
            wall_list_kb = Constructor.create_inline_kb(
                [
                    {
                        "text": f"{wall.source_short_name}",
                        "cb": ({"idx": wall.idx, "action": "wall_view"}, vk_wall_manage_cb),
                    }
                    for wall in walls
                ],
                [1] * len(walls),
            )
            wall_list_kb.add(back_to_vk_main_menu_kb.inline_keyboard[-1][0])
        else:
            wall_list_kb = back_to_vk_main_menu_kb
        await query.message.edit_text(
            f"Ваши стены\nЗанято {len(walls)} из {walls_headers.max_count} слотов.\n"
            f"Выбери стену для управления её состоянием.",
            reply_markup=wall_list_kb,
        )


@dp.message_handler(state=UserVkSettings.add_wall_id)
async def fsm_user_add_vk_wall(message: Message, state: FSMContext):
    wall_id = await UserVkSettings.get_wall_id_from_public_url(message.text)
    if not wall_id:
        return await message.answer(
            f"{hbold('Ошибка')}\n\nСтена или сообщество не найдено\n\nПопробуй снова",
            reply_markup=back_to_vk_main_menu_kb,
        )
    await UserVkSettings.next()
    await state.update_data({"wall_short_name": message.text, "wall_id": wall_id, "idx": str(uuid4())})
    await message.answer(
        f"Введи {hbold('telegram_id')}\n"
        "Чтобы узнать свой или id группы, воспользуйся @myidbot @getmyid_bot\n\n"
        f"Для возможности репостов в определенный телеграмм канал/группу, "
        f"бот должен быть участником нужного чата и иметь в нем {hbold('права администратора')}",
        reply_markup=back_to_vk_main_menu_kb,
    )


@dp.message_handler(state=UserVkSettings.add_telegram_id)
async def fsm_user_set_telegram_id(message: Message, state: FSMContext):
    chat_id, error = await UserVkSettings.get_telegram_id(message.text)
    if error:
        return await message.answer(
            f"{hbold('Ошибка')}\n\n{error}\n\nПопробуй снова", reply_markup=back_to_vk_main_menu_kb
        )
    await UserVkSettings.next()
    await state.update_data({"tg_id": chat_id})
    state_data = await state.get_data()
    await message.answer(
        "Выбери, с какой периодичностью нужно опрашивать стену.",
        reply_markup=get_wall_timeout_kb(state_data["idx"]),
    )


@dp.callback_query_handler(vk_wall_params_cb.filter(), state=UserVkSettings.add_timeout)
async def fsm_user_set_vk_sleep(
    query: CallbackQuery, callback_data: dict, subscriber: Subscriber, state: FSMContext
):
    await UserVkSettings.next()
    await state.update_data({"sleep": callback_data["timeout"]})
    await query.message.edit_text(
        "Выбери количество постов, которое нужно получить со стены.\n"
        f"Для твоего уровня подписки '{subscriber.level}' доступны следующие варианты.\n\n"
        f"{hbold('Default - последний пост в заданный таймаут.')}",
        reply_markup=get_wall_fetch_count_kb(callback_data["idx"], subscriber.level),
    )


@dp.callback_query_handler(vk_wall_params_cb.filter(), state=UserVkSettings.add_fetch_count)
async def fsm_user_set_fetch_count(
    query: CallbackQuery, callback_data: dict, subscriber: Subscriber, state: FSMContext
):
    fsm_store = await state.get_data()
    await state.finish()
    try:
        await crud.target.add_source(
            schemas.ForwardCreate(
                idx=fsm_store["idx"],
                target_id=subscriber.id,
                source_id=fsm_store["wall_id"],
                source_short_name=fsm_store["wall_short_name"],
                source_type="vk",
                to_chat_id=fsm_store["tg_id"],
                sleep=fsm_store["sleep"],
                fetch_count=callback_data["fetch_count"],
            )
        )
    except ValueError:
        return await query.message.edit_text(
            "Ошибка!\nТакая стена уже существует", reply_markup=vk_main_menu_kb
        )
    await query.message.edit_text(
        'Успешно!\nЧтобы начать репосты, откройте список стен, выберите нужную и нажмите "Старт"',
        reply_markup=vk_main_menu_kb,
    )


@dp.callback_query_handler(vk_wall_manage_cb.filter())
async def cq_user_manage_vk_wall(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    wall_idx = callback_data["idx"]
    wall_info = await crud.target.get_source_by_idx(subscriber.id, wall_idx)
    try:
        to_channel_link = await dp.bot.export_chat_invite_link(wall_info.to_chat_id)
    except BadRequest:
        to_channel_link = wall_info.to_chat_id
    message_text = (
        f"Стена: {wall_info.source_short_name}\n"
        f"репосты в канал: {to_channel_link}\nтаймаут: {wall_info.sleep} мин\n"
        f"кол-во собираемых постов (fetch count): {wall_info.fetch_count}"
    )

    if action == "wall_view":
        wall_status = vk_broadcaster.is_wall_active(
            query.from_user.id, wall_info.source_id, wall_info.to_chat_id
        )
        alias = {True: "работает", False: "остановлено"}
        wall_manage_kb = get_wall_manage_kb(wall_idx, wall_status)
        await query.message.edit_text(
            f"{message_text}\nстатус: {hbold(alias[wall_status])}", reply_markup=wall_manage_kb
        )

    if action == "wall_start":
        await vk_broadcaster.start_fetch_wall(
            job_data=(
                query.from_user.id,
                wall_info.source_id,
                wall_info.to_chat_id,
                wall_info.sleep,
                wall_info.fetch_count,
            )
        )
        wall_manage_kb = get_wall_manage_kb(wall_idx, True)
        await query.message.edit_text(
            f"{message_text}\nстатус: {hbold('работает')}", reply_markup=wall_manage_kb
        )

    if action == "wall_stop":
        vk_broadcaster.stop_fetch_wall(query.from_user.id, wall_info.source_id, wall_info.to_chat_id)
        wall_manage_kb = get_wall_manage_kb(wall_idx, False)
        await query.message.edit_text(
            f"{message_text}\nстатус: {hbold('остановлено')}", reply_markup=wall_manage_kb
        )

    if action == "wall_del":
        await crud.target.remove_source_data(subscriber.id, wall_idx)
        await vk_broadcaster.remove_wall(query.from_user.id, wall_info.source_id, wall_info.to_chat_id)
        await query.message.edit_text("Стена удалена", reply_markup=vk_main_menu_kb)

    if action == "wall_ch_timeout":
        await query.message.edit_text("Выберите новое значение", reply_markup=get_wall_timeout_kb(wall_idx))

    if action == "wall_ch_fetch_count":
        await query.message.edit_text(
            "Выберите новое значение", reply_markup=get_wall_fetch_count_kb(wall_idx, 0)
        )


@dp.callback_query_handler(vk_wall_params_cb.filter())
async def cq_user_change_wall_params(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    wall_info = await crud.target.get_source_by_idx(subscriber.id, callback_data["idx"])

    if callback_data["timeout"] != "_":
        await crud.target.update_source_data(
            schemas.ForwardUpdate(
                idx=wall_info.idx,
                target_id=subscriber.id,
                source_id=wall_info.source_id,
                sleep=int(callback_data["timeout"]),
            )
        )
    elif callback_data["fetch_count"] != "_":
        await crud.target.update_source_data(
            schemas.ForwardUpdate(
                idx=wall_info.idx,
                target_id=subscriber.id,
                source_id=wall_info.source_id,
                fetch_count=int(callback_data["fetch_count"]),
            )
        )

    await query.message.edit_text("Успешно! Перезапустите стену", reply_markup=vk_main_menu_kb)


@dp.callback_query_handler(actions_cb.filter(action=["twitter_main", "instagram_main"]))
async def cq_user_twitter_main(query: CallbackQuery):
    await query.message.edit_text("В разработке", reply_markup=twitter_main_menu_kb)
