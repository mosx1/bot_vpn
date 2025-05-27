# from connect import engine

# from sqlalchemy import Column,Numeric, BIGINT, TEXT, TIMESTAMP, BOOLEAN, CHAR, ForeignKeyConstraint
# from sqlalchemy.ext.declarative import declarative_base



# Base = declarative_base()

# class User(Base):

#     __tablename__: str = 'users_subscription'

#     telegram_id: Column = Column(BIGINT, primary_key=True)
#     name: Column = Column(TEXT, nullable=True)
#     exit_date: Column = Column(TIMESTAMP, nullable=False)
#     action: Column = Column(BOOLEAN, nullable=False)
#     server_link: Column = Column(TEXT, nullable=False)
#     server_id: Column = Column(BIGINT, nullable=False)
#     server_desired: Column = Column(CHAR, nullable=True)
#     paid: Column = Column(BOOLEAN, nullable=False)
#     protocol: Column = Column(BIGINT, nullable=False)
#     statistic: Column = Column(TEXT, nullable=True)
#     balance: Column = Column(Numeric, nullable=True)
#     invited: Column = Column(BIGINT, nullable=True)

#     __table_args__ = (
#         ForeignKeyConstraint(['invited'], ['telegram_id']),
#     )
    
    
# Base.metadata.create_all(engine)
#     # def save(self):
#     #     with db.cursor(cursor_factory=DictCursor) as cursor:
#     #         cursor.execute(f"UPDATE users_subscription SET * FROM users_subscription WHERE telegram_id = {self.telegramId}")
    