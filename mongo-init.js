db.createUser(
    {
        user: 'root-coppel',
        pwd: 'password-coppel',
        roles: [
            { role: "clusterMonitor", db: "admin" },
            { role: "dbOwner", db: "db_name" },
            { role: 'readWrite', db: 'db_coppel' }
        ]
    }
)