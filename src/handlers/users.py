import logging

from aiogram import Router, types
from magic_filter import F
from aiogram.dispatcher.fsm.context import FSMContext

from src.utils.callbacks import (
    Actions,
    MainUserMenu,
    VkActionsMenu,
    UserMenuCallback,
    ProvidersUserMenu,
    VkServiceMenuCallback,
)
from src.handlers.markups import user_markups

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(UserMenuCallback.filter(F.action == Actions.idle), state="*")
async def cq_user_main_menu(query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await query.message.edit_text("Выбери действие", reply_markup=user_markups.main_menu)


@router.callback_query(UserMenuCallback.filter(F.main_nav))
async def cq_user_main_service_menu(query: types.CallbackQuery, callback_data: UserMenuCallback):
    match callback_data.main_nav:
        case MainUserMenu.start:
            await query.message.edit_text(
                "Доступные сервисы", reply_markup=user_markups.provider_services_menu
            )
        case MainUserMenu.faq:
            await query.message.edit_text("Помощь", reply_markup=user_markups.back_to_idle(once=True))
        case MainUserMenu.settings:
            await query.message.edit_text("Настройки", reply_markup=user_markups.settings_menu)


@router.callback_query(UserMenuCallback.filter(F.providers_nav))
async def cq_user_providers_menu(query: types.CallbackQuery, callback_data: UserMenuCallback):
    providers_menu_nav = callback_data.providers_nav
    match providers_menu_nav:
        case ProvidersUserMenu.vkontakte:
            await query.message.edit_text("ВКонтакте", reply_markup=user_markups.vk_main_menu)
        case ProvidersUserMenu.twitter:
            pass
        case ProvidersUserMenu.instagram:
            pass
        case ProvidersUserMenu.telegram:
            pass


@router.callback_query(VkServiceMenuCallback.filter())
async def cq_user_vk_service(query: types.CallbackQuery, callback_data: VkServiceMenuCallback):
    main_nav = callback_data.main_nav
    match main_nav:
        case VkActionsMenu.view:
            await query.message.edit_text("Просмотр стен")
        case Actions.back:
            await query.message.edit_text("Доступные сервисы", reply_markup=user_markups.provider_services_menu)
