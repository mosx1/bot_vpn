"""
Репозитории для работы с БД по сущностям.
"""
from database.repositories.base_repository import BaseRepository
from database.repositories.user_repository import user_repository
from database.repositories.server_repository import server_repository
from database.repositories.user_to_subscription_repository import user_to_subscription_repository
from database.repositories.security_hash_repository import security_hash_repository
from database.repositories.gift_code_repository import gift_code_repository
from database.repositories.sale_invoice_repository import sale_invoice_repository
from database.repositories.invite_repository import invite_repository

# Функции-обёртки для обратной совместимости
get_user_by_id = user_repository.get_user_by_id
get_user_by = user_repository.get_user_by
get_user_by_country = user_repository.get_user_by_country
reduce_time_by = user_repository.reduce_time_by
insert_user = user_repository.insert_user
update_user_extend_subscription = user_repository.update_user_extend_subscription
update_user_deactivate = user_repository.update_user_deactivate
get_inactive_users_by_server = user_repository.get_inactive_users_by_server
update_user_renewal = user_repository.update_user_renewal
check_user_has_active_subscription = user_repository.check_user_has_active_subscription
get_all_telegram_ids = user_repository.get_all_telegram_ids
get_active_users_by_server = user_repository.get_active_users_by_server
update_user_server_link = user_repository.update_user_server_link
update_user_server_and_link = user_repository.update_user_server_and_link
delete_user = user_repository.delete_user

add_subscription_for_user = user_to_subscription_repository.add_subscription_for_user

get_server_list = server_repository.get_server_list
get_country_list = server_repository.get_country_list
get_server_name_by_id = server_repository.get_server_name_by_id
get_server_url_by_id = server_repository.get_server_url_by_id
get_very_free_server = server_repository.get_very_free_server
get_info_all_servers = server_repository.get_info_all_servers
get_info_servers = server_repository.get_info_servers
update_answers_servers = server_repository.update_answers_servers

get_token = security_hash_repository.get_token

gen_gift_code = gift_code_repository.gen_gift_code
check_and_consume_gift_code = gift_code_repository.check_and_consume_gift_code

add_sale_invoice = sale_invoice_repository.add_sale_invoice
get_invoices_with_expiry = sale_invoice_repository.get_invoices_with_expiry
delete_invoice = sale_invoice_repository.delete_invoice

write_invited = invite_repository.write_invited
increment_balance = invite_repository.increment_balance
reset_to_zero_balance = invite_repository.reset_to_zero_balance

__all__ = [
    'BaseRepository',
    'user_repository',
    'server_repository',
    'user_to_subscription_repository',
    'security_hash_repository',
    'gift_code_repository',
    'sale_invoice_repository',
    'invite_repository',
    'get_user_by_id',
    'get_user_by',
    'get_user_by_country',
    'reduce_time_by',
    'insert_user',
    'update_user_extend_subscription',
    'update_user_deactivate',
    'get_inactive_users_by_server',
    'update_user_renewal',
    'check_user_has_active_subscription',
    'get_all_telegram_ids',
    'get_active_users_by_server',
    'update_user_server_link',
    'update_user_server_and_link',
    'delete_user',
    'add_subscription_for_user',
    'get_server_list',
    'get_country_list',
    'get_server_name_by_id',
    'get_server_url_by_id',
    'get_very_free_server',
    'get_info_all_servers',
    'get_info_servers',
    'update_answers_servers',
    'get_token',
    'gen_gift_code',
    'check_and_consume_gift_code',
    'add_sale_invoice',
    'get_invoices_with_expiry',
    'delete_invoice',
    'write_invited',
    'increment_balance',
    'reset_to_zero_balance',
]
