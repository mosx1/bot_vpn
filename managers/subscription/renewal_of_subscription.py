from connect import db

import controllerFastApi, config



def renewalOfSubscription(userId, serverId, intervalSql: str, serverNew=None):
    
    sqlTextLink = ""

    if serverNew != None and serverId != serverNew:
        
        controllerFastApi.delUser(userId, serverId)
        link = controllerFastApi.add_vpn_user(userId, serverNew)
        sqlTextLink = ", server_link='" + link + "'"

    else:

        controllerFastApi.resumeUser(userId, serverId)

    with db.cursor() as cursor:   
        cursor.execute("UPDATE users_subscription" + 
                    "\nSET exit_date= now() " + str(intervalSql) +
                    ",action=True, paid=True" + 
                    sqlTextLink + 
                    ", server_id = '" + str(serverId) + "'" +
                    ", protocol=" + str(config.DEFAULTPROTOCOL) + 
                    "\nWHERE telegram_id=" + str(userId))
        db.commit()