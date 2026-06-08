"""Server 包初始化。

通过将 PyMySQL 安装为 MySQLdb 的替代品来修补 MySQL 数据库驱动，
使 Django 的 MySQL 后端在无需原生 mysqlclient C 扩展的情况下运行。
"""
import pymysql

pymysql.install_as_MySQLdb()

print("===============install pymysql==============")
