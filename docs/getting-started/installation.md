---
layout: default
title: Install Soda SQL
parent: Get Started
nav_order: 1
---

# Install Soda SQL

Soda SQL is a command-line interface (CLI) tool that enables you to scan the data in your database to surface invalid, missing, or unexpected data. 
<br />

**[Compatibility](#ccompatibility)<br />
[Requirements](#requirements)<br />
[Install](#install)<br />
[Upgrade](#upgrade)<br />
[Troubleshoot](#troubleshoot)<br />
[Go further](#go-further)<br />**

## Compatibility

Use Soda SQL with any of the following data warehouses:

- Apache Hive
- AWS Athena
- AWS Redshift
- Google Cloud Platform BigQuery
- Microsoft SQL Server
- PostgreSQL
- Snowflake


## Requirements

To use Soda SQL, you must have installed the following on your system:
- **Python 3.7** or greater. To check your existing version, use the CLI command: `python --version`
- **Pip 21.0** or greater. To check your existing version, use the CLI command: `pip --version`

For Linux users only, install the following:
- On Debian Buster: `apt-get install g++ unixodbc-dev python3-dev libssl-dev libffi-dev`
- On CentOS 8: `yum install gcc-c++ unixODBC-devel python38-devel libffi-devel openssl-devel`

For MSSQL Server users only, install the following:
- [SQLServer Driver](https://docs.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server?view=sql-server-ver15)


## Install

From your command-line interface tool, execute the following command:

```
$ pip install soda-sql
```

Optionally, you can install Soda SQL in a virtual environment. Execute the following commands one by one:

```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install soda-sql
```


## Upgrade 

To upgrade your existing Soda SQL tool to the latest version, use the following command:
```shell
pip install soda-sql -U
```

## Troubleshoot

**Problem:** There are known issues on Soda SQL when using pip version 19. <br />
**Solution:** Upgrade `pip` to version 20 or greater using the following command:
```shell
$ pip install --upgrade pip
```
<br />

**Problem:** Upgrading Soda SQL does not seem to work. <br />
**Solution:** Run the following command to skip your local cache when upgrading your Soda SQL version:
```shell
$ pip install --upgrade --no-cache-dir soda-sql
```

## Go further

* Set up Soda SQL and run your first scan: [Quick start tutorial]({% link getting-started/5_min_tutorial.md %})
* Learn [How Soda SQL works]({% link documentation/concepts.md %}).