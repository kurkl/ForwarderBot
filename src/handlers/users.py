from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold

from src.runner import dp
from src.database import crud, schemas
from src.utils.keyboards import Constructor
from src.database.entities import Subscriber
from src.services.vk.public import vk_scheduler

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
            await UserVkData.set_wall_id.set()
            await query.message.edit_text(
                f"Доступно {len(walls)}/{walls_headers.max_count} стен\n"
                f"Введи короткое имя стены, к примеру, для стены vk.com/durov нужно ввести только durov",
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
                        "text": f"{wall.source_short_name} tg_id: {wall.to_chat_id}",
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
            f"Ваши стены\nЗанято {len(walls)} из {walls_headers.max_count} слотов.\n"
            f"Выбери стену для управления её состоянием.",
            reply_markup=walls_kb,
        )


@dp.message_handler(state=UserVkData.set_wall_id)
async def fsm_user_add_vk_wall(message: Message, state: FSMContext):
    wall_id = await UserVkData.get_wall_id_from_domain(message.text)
    if not wall_id:
        return await message.reply(
            f"{hbold('Ошибка')}\n\nСтена или сообщество не найдено\n\nПопробуй снова",
            reply_markup=back_to_vk_main_menu_kb,
        )
    await UserVkData.next()
    await state.update_data({"wall_short_name": message.text, "wall_id": wall_id})
    await message.answer(
        f"Введи {hbold('telegram_id')}\n"
        "Чтобы узнать свой или id группы, воспользуйся @myidbot @getmyid_bot\n\n"
        f"Для возможности репостов в определенный телеграмм канал/группу, "
        f"бот должен быть участником нужного чата и иметь в нем {hbold('права администратора')}",
        reply_markup=back_to_vk_main_menu_kb,
    )


@dp.message_handler(state=UserVkData.set_telegram_id)
async def fsm_user_set_telegram_id(message: Message, state: FSMContext):
    chat_id, error = await UserVkData.get_telegram_id(message.text)
    if error:
        return await message.reply(
            f"{hbold('Ошибка')}\n\n{error}\n\nПопробуй снова", reply_markup=back_to_vk_main_menu_kb
        )
    await UserVkData.next()
    await state.update_data({"tg_id": chat_id})
    await message.answer(
        "Выбери, с какой периодичностью нужно опрашивать стену.", reply_markup=vk_walls_timeouts_kb
    )


@dp.callback_query_handler(vk_wall_cb.filter(), state=UserVkData.set_sleep)
async def fsm_user_set_vk_sleep(
    query: CallbackQuery, callback_data: dict, subscriber: Subscriber, state: FSMContext
):
    await UserVkData.next()
    await state.update_data({"sleep": callback_data["time"]})
    await query.message.edit_text(
        "Выбери количество постов, которое нужно получить со стены.\n"
        f"Для твоего уровня подписки '{subscriber.level}' доступны следующие варианты.\n\n"
        f"{hbold('Default - последний пост в заданный таймаут.')}",
        reply_markup=get_wall_fetch_count_kb(subscriber.level),
    )


@dp.callback_query_handler(vk_fetch_count_cb.filter(), state=UserVkData.set_fetch_count)
async def fsm_user_set_fetch_count(
    query: CallbackQuery, callback_data: dict, subscriber: Subscriber, state: FSMContext
):
    fsm_store = await state.get_data()
    await crud.target.add_source(
        schemas.ForwardCreate(
            target_id=subscriber.id,
            source_id=fsm_store["wall_id"],
            source_short_name=fsm_store["wall_short_name"],
            source_type="vk",
            to_chat_id=fsm_store["tg_id"],
            sleep=fsm_store["sleep"],
            fetch_count=callback_data["count"],
        )
    )
    await state.finish()
    await query.message.edit_text(
        'Успешно!\nЧтобы начать репосты, откройте список стен, выберите нужную и нажмите "Старт"',
        reply_markup=vk_main_menu_kb,
    )


@dp.callback_query_handler(vk_wall_manage_cb.filter())
async def cq_user_manage_vk_wall(query: CallbackQuery, subscriber: Subscriber, callback_data: dict):
    action = callback_data["action"]
    wall_id = int(callback_data["id"])
    wall_info = await crud.target.get_source_data(wall_id, subscriber.id)

    if action == "wall_view":
        wall_manage_kb = get_wall_manage_kb(wall_id)
        await query.message.edit_text(
            f"Стена: https://vk.com/{wall_info.source_short_name}\nid: {wall_info.source_id}\n"
            f"репосты в канал: {wall_info.to_chat_id}\nтаймаут: {wall_info.sleep} мин",
            reply_markup=wall_manage_kb,
        )

    if action == "wall_start":
        await vk_scheduler.add_job(
            query.from_user.id, wall_id, wall_info.to_chat_id, wall_info.sleep, wall_info.fetch_count
        )
        await query.answer("Запущено")

    if action == "wall_remove":
        await crud.target.remove_source_data(wall_id, wall_info.target_id)
        await vk_scheduler.remove_job(query.from_user.id, wall_id, wall_info.to_chat_id)
        await query.message.edit_text("Удалено", reply_markup=vk_main_menu_kb)

    if action == "wall_pause":
        vk_scheduler.pause_job(query.from_user.id, wall_id, wall_info.to_chat_id)
        await query.answer("Остановлено", show_alert=True)

    if action == "wall_resume":
        vk_scheduler.continue_job(query.from_user.id, wall_id, wall_info.to_chat_id)
        await query.answer("Восстановлено", show_alert=True)


@dp.callback_query_handler(actions_cb.filter(action="twitter_main"))
async def cq_user_twitter_main(query: CallbackQuery):
    await query.message.edit_text("В разработке", reply_markup=twitter_main_menu_kb)
