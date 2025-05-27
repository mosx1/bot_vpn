from connect import db

import controllerFastApi, config



def renewalOfSubscription(userId, serverId, intervalSql: str, serverNew=None) -> bool:
    
    sqlTextLink = ""

    if serverNew == None:
        serverNew = serverId

    if serverId != serverNew:
        
        controllerFastApi.del_users({userId}, serverId)
        link = controllerFastApi.add_vpn_user(userId, serverNew)
        sqlTextLink = ", server_link='" + link + "'"

    else:

        controllerFastApi.resumeUser(userId, serverId)

    with db.cursor() as cursor:   
        cursor.execute("UPDATE users_subscription" + 
                    "\nSET exit_date=" +
                    "\nCASE WHEN exit_date > now()" +
                    "\nTHEN exit_date" + str(intervalSql) +
                    "\nELSE now()" + str(intervalSql) +
                    "\nEND,action=True, paid=True" + 
                    sqlTextLink + 
                    ", server_id = '" + str(serverNew) + "'" +
                    ", protocol=" + str(config.DEFAULTPROTOCOL) + 
                    "\nWHERE telegram_id=" + str(userId))
        db.commit()