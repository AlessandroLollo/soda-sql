#  Copyright 2020 Soda
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import re

import psycopg2

from sodasql.scan.dialect import Dialect, POSTGRES, KEY_WAREHOUSE_TYPE, KEY_CONNECTION_TIMEOUT
from sodasql.scan.parser import Parser


class PostgresDialect(Dialect):

    def __init__(self, parser: Parser = None, type: str = POSTGRES):
        super().__init__(type)
        if parser:
            self.host = parser.get_str_optional_env('host', 'localhost')
            self.port = parser.get_str_optional_env('port', '5432')
            self.username = parser.get_str_required_env('username')
            self.password = parser.get_credential('password')
            self.database = parser.get_str_required_env('database')
            self.schema = parser.get_str_required_env('schema')
            self.connection_timeout = parser.get_int_optional(KEY_CONNECTION_TIMEOUT)

    def default_connection_properties(self, params: dict):
        return {
            KEY_WAREHOUSE_TYPE: POSTGRES,
            'host': 'localhost',
            'port': '5432',
            'username': 'env_var(POSTGRES_USERNAME)',
            'password': 'env_var(POSTGRES_PASSWORD)',
            'database': params.get('database', 'your_database'),
            'schema': 'public'
        }

    def default_env_vars(self, params: dict):
        return {
            'POSTGRES_USERNAME': params.get('username', 'Eg johndoe'),
            'POSTGRES_PASSWORD': params.get('password', 'Eg abc123')
        }

    def sql_tables_metadata_query(self, limit: str = 10, filter: str = None):
        return (f"SELECT table_name \n"
                f"FROM information_schema.tables \n"
                f"WHERE lower(table_schema)='{self.schema.lower()}'")

    def create_connection(self):
        try:
            conn = psycopg2.connect(
                user=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
                connect_timeout=self.connection_timeout,
                options=f'-c search_path={self.schema}' if self.schema else None)
            return conn
        except Exception as e:
            self.try_to_raise_soda_sql_exception(e)

    def sql_columns_metadata_query(self, table_name: str) -> str:
        sql = (f"SELECT column_name, data_type, is_nullable \n"
               f"FROM information_schema.columns \n"
               f"WHERE lower(table_name) = '{table_name}'")
        if self.database:
            sql += f" \n  AND table_catalog = '{self.database}'"
        if self.schema:
            sql += f" \n  AND table_schema = '{self.schema}'"
        return sql

    def qualify_table_name(self, table_name: str) -> str:
        if self.schema:
            return f'"{self.schema}"."{table_name}"'
        return f'"{table_name}"'

    def qualify_column_name(self, column_name: str):
        return f'"{column_name}"'

    def sql_expr_regexp_like(self, expr: str, pattern: str):
        return f"{expr} ~* '{self.qualify_regex(pattern)}'"

    def sql_expr_cast_text_to_number(self, quoted_column_name, validity_format):
        if validity_format == 'number_whole':
            return f"CAST({quoted_column_name} AS {self.data_type_decimal})"
        not_number_pattern = self.qualify_regex(r"[^-\d\.\,]")
        comma_pattern = self.qualify_regex(r"\,")
        return f"CAST(REGEXP_REPLACE(REGEXP_REPLACE({quoted_column_name}, '{not_number_pattern}', '', 'g'), " \
               f"'{comma_pattern}', '.', 'g') AS {self.data_type_decimal})"

    def get_type_name(self, column_description):
        return PostgresDialect.type_names_by_type_code.get(str(column_description[1]))

    def is_connection_error(self, exception):
        if exception is None:
            return False
        error_message = str(exception)
        return error_message.find('Operation timed out') != -1 or \
               error_message.find('could not translate host name') != -1 or \
               error_message.find('could not connect to server') != -1 or \
               error_message.find('No route to host') != -1 or \
               error_message.find('no route to host') != -1 or \
               error_message.find('timeout expired') != -1

    def is_authentication_error(self, exception):
        if exception is None:
            return False
        error_message = str(exception)
        return error_message.find('Connection refused') != -1 or \
               error_message.find('password authentication failed') != -1 or \
               re.search('role ".*" does not exist', error_message)

    type_names_by_type_code = {
        '16': 'bool',
        '17': 'bytea',
        '18': 'char',
        '19': 'name',
        '20': 'int8',
        '21': 'int2',
        '22': 'int2vector',
        '23': 'int4',
        '24': 'regproc',
        '25': 'text',
        '26': 'oid',
        '27': 'tid',
        '28': 'xid',
        '29': 'cid',
        '30': 'oidvector',
        '32': 'pg_ddl_command',
        '71': 'pg_type',
        '75': 'pg_attribute',
        '81': 'pg_proc',
        '83': 'pg_class',
        '114': 'json',
        '142': 'xml',
        '143': '_xml',
        '194': 'pg_node_tree',
        '199': '_json',
        '210': 'smgr',
        '325': 'index_am_handler',
        '600': 'point',
        '601': 'lseg',
        '602': 'path',
        '603': 'box',
        '604': 'polygon',
        '628': 'line',
        '629': '_line',
        '650': 'cidr',
        '651': '_cidr',
        '700': 'float4',
        '701': 'float8',
        '702': 'abstime',
        '703': 'reltime',
        '704': 'tinterval',
        '705': 'unknown',
        '718': 'circle',
        '719': '_circle',
        '790': 'money',
        '791': '_money',
        '829': 'macaddr',
        '869': 'inet',
        '1000': '_bool',
        '1001': '_bytea',
        '1002': '_char',
        '1003': '_name',
        '1005': '_int2',
        '1006': '_int2vector',
        '1007': '_int4',
        '1008': '_regproc',
        '1009': '_text',
        '1010': '_tid',
        '1011': '_xid',
        '1012': '_cid',
        '1013': '_oidvector',
        '1014': '_bpchar',
        '1015': '_varchar',
        '1016': '_int8',
        '1017': '_point',
        '1018': '_lseg',
        '1019': '_path',
        '1020': '_box',
        '1021': '_float4',
        '1022': '_float8',
        '1023': '_abstime',
        '1024': '_reltime',
        '1025': '_tinterval',
        '1027': '_polygon',
        '1028': '_oid',
        '1033': 'aclitem',
        '1034': '_aclitem',
        '1040': '_macaddr',
        '1041': '_inet',
        '1042': 'bpchar',
        '1043': 'varchar',
        '1082': 'date',
        '1083': 'time',
        '1114': 'timestamp',
        '1115': '_timestamp',
        '1182': '_date',
        '1183': '_time',
        '1184': 'timestamptz',
        '1185': '_timestamptz',
        '1186': 'interval',
        '1187': '_interval',
        '1231': '_numeric',
        '1248': 'pg_database',
        '1263': '_cstring',
        '1266': 'timetz',
        '1270': '_timetz',
        '1560': 'bit',
        '1561': '_bit',
        '1562': 'varbit',
        '1563': '_varbit',
        '1700': 'numeric',
        '1790': 'refcursor',
        '2201': '_refcursor',
        '2202': 'regprocedure',
        '2203': 'regoper',
        '2204': 'regoperator',
        '2205': 'regclass',
        '2206': 'regtype',
        '2207': '_regprocedure',
        '2208': '_regoper',
        '2209': '_regoperator',
        '2210': '_regclass',
        '2211': '_regtype',
        '2249': 'record',
        '2275': 'cstring',
        '2276': 'any',
        '2277': 'anyarray',
        '2278': 'void',
        '2279': 'trigger',
        '2280': 'language_handler',
        '2281': 'internal',
        '2282': 'opaque',
        '2283': 'anyelement',
        '2287': '_record',
        '2776': 'anynonarray',
        '2842': 'pg_authid',
        '2843': 'pg_auth_members',
        '2949': '_txid_snapshot',
        '2950': 'uuid',
        '2951': '_uuid',
        '2970': 'txid_snapshot',
        '3115': 'fdw_handler',
        '3220': 'pg_lsn',
        '3221': '_pg_lsn',
        '3310': 'tsm_handler',
        '3500': 'anyenum',
        '3614': 'tsvector',
        '3615': 'tsquery',
        '3642': 'gtsvector',
        '3643': '_tsvector',
        '3644': '_gtsvector',
        '3645': '_tsquery',
        '3734': 'regconfig',
        '3735': '_regconfig',
        '3769': 'regdictionary',
        '3770': '_regdictionary',
        '3802': 'jsonb',
        '3807': '_jsonb',
        '3831': 'anyrange',
        '3838': 'event_trigger',
        '3904': 'int4range',
        '3905': '_int4range',
        '3906': 'numrange',
        '3907': '_numrange',
        '3908': 'tsrange',
        '3909': '_tsrange',
        '3910': 'tstzrange',
        '3911': '_tstzrange',
        '3912': 'daterange',
        '3913': '_daterange',
        '3926': 'int8range',
        '3927': '_int8range',
        '4066': 'pg_shseclabel',
        '4089': 'regnamespace',
        '4090': '_regnamespace',
        '4096': 'regrole',
        '4097': '_regrole',
        '10000': 'pg_attrdef',
        '10001': 'pg_constraint',
        '10002': 'pg_inherits',
        '10003': 'pg_index',
        '10004': 'pg_operator',
        '10005': 'pg_opfamily',
        '10006': 'pg_opclass',
        '10156': 'pg_am',
        '10157': 'pg_amop',
        '10846': 'pg_amproc',
        '11393': 'pg_language',
        '11394': 'pg_largeobject_metadata',
        '11395': 'pg_largeobject',
        '11396': 'pg_aggregate',
        '11397': 'pg_statistic',
        '11398': 'pg_rewrite',
        '11399': 'pg_trigger',
        '11400': 'pg_event_trigger',
        '11401': 'pg_description',
        '11402': 'pg_cast',
        '11616': 'pg_enum',
        '11617': 'pg_namespace',
        '11618': 'pg_conversion',
        '11619': 'pg_depend',
        '11620': 'pg_db_role_setting',
        '11621': 'pg_tablespace',
        '11622': 'pg_pltemplate',
        '11623': 'pg_shdepend',
        '11624': 'pg_shdescription',
        '11625': 'pg_ts_config',
        '11626': 'pg_ts_config_map',
        '11627': 'pg_ts_dict',
        '11628': 'pg_ts_parser',
        '11629': 'pg_ts_template',
        '11630': 'pg_extension',
        '11631': 'pg_foreign_data_wrapper',
        '11632': 'pg_foreign_server',
        '11633': 'pg_user_mapping',
        '11634': 'pg_foreign_table',
        '11635': 'pg_policy',
        '11636': 'pg_replication_origin',
        '11637': 'pg_default_acl',
        '11638': 'pg_init_privs',
        '11639': 'pg_seclabel',
        '11640': 'pg_collation',
        '11641': 'pg_range',
        '11642': 'pg_transform',
        '11643': 'pg_toast_2604',
        '11644': 'pg_toast_2606',
        '11645': 'pg_toast_2609',
        '11646': 'pg_toast_1255',
        '11647': 'pg_toast_2618',
        '11648': 'pg_toast_3596',
        '11649': 'pg_toast_2619',
        '11650': 'pg_toast_2620',
        '11651': 'pg_toast_2396',
        '11652': 'pg_toast_2964',
        '11653': 'pg_toast_3592',
        '11655': 'pg_roles',
        '11659': 'pg_shadow',
        '11662': 'pg_group',
        '11665': 'pg_user',
        '11668': 'pg_policies',
        '11672': 'pg_rules',
        '11676': 'pg_views',
        '11680': 'pg_tables',
        '11684': 'pg_matviews',
        '11688': 'pg_indexes',
        '11692': 'pg_stats',
        '11696': 'pg_locks',
        '11699': 'pg_cursors',
        '11702': 'pg_available_extensions',
        '11705': 'pg_available_extension_versions',
        '11708': 'pg_prepared_xacts',
        '11712': 'pg_prepared_statements',
        '11715': 'pg_seclabels',
        '11719': 'pg_settings',
        '11724': 'pg_file_settings',
        '11727': 'pg_timezone_abbrevs',
        '11730': 'pg_timezone_names',
        '11733': 'pg_config',
        '11736': 'pg_stat_all_tables',
        '11740': 'pg_stat_xact_all_tables',
        '11744': 'pg_stat_sys_tables',
        '11748': 'pg_stat_xact_sys_tables',
        '11751': 'pg_stat_user_tables',
        '11755': 'pg_stat_xact_user_tables',
        '11758': 'pg_statio_all_tables',
        '11762': 'pg_statio_sys_tables',
        '11765': 'pg_statio_user_tables',
        '11768': 'pg_stat_all_indexes',
        '11772': 'pg_stat_sys_indexes',
        '11775': 'pg_stat_user_indexes',
        '11778': 'pg_statio_all_indexes',
        '11782': 'pg_statio_sys_indexes',
        '11785': 'pg_statio_user_indexes',
        '11788': 'pg_statio_all_sequences',
        '11792': 'pg_statio_sys_sequences',
        '11795': 'pg_statio_user_sequences',
        '11798': 'pg_stat_activity',
        '11802': 'pg_stat_replication',
        '11806': 'pg_stat_wal_receiver',
        '11809': 'pg_stat_ssl',
        '11812': 'pg_replication_slots',
        '11816': 'pg_stat_database',
        '11819': 'pg_stat_database_conflicts',
        '11822': 'pg_stat_user_functions',
        '11826': 'pg_stat_xact_user_functions',
        '11830': 'pg_stat_archiver',
        '11833': 'pg_stat_bgwriter',
        '11836': 'pg_stat_progress_vacuum',
        '11840': 'pg_user_mappings',
        '11844': 'pg_replication_origin_status',
        '12129': 'cardinal_number',
        '12131': 'character_data',
        '12132': 'sql_identifier',
        '12134': 'information_schema_catalog_name',
        '12136': 'time_stamp',
        '12137': 'yes_or_no',
        '12140': 'applicable_roles',
        '12144': 'administrable_role_authorizations',
        '12147': 'attributes',
        '12151': 'character_sets',
        '12155': 'check_constraint_routine_usage',
        '12159': 'check_constraints',
        '12163': 'collations',
        '12166': 'collation_character_set_applicability',
        '12169': 'column_domain_usage',
        '12173': 'column_privileges',
        '12177': 'column_udt_usage',
        '12181': 'columns',
        '12185': 'constraint_column_usage',
        '12189': 'constraint_table_usage',
        '12193': 'domain_constraints',
        '12197': 'domain_udt_usage',
        '12200': 'domains',
        '12204': 'enabled_roles',
        '12207': 'key_column_usage',
        '12211': 'parameters',
        '12215': 'referential_constraints',
        '12219': 'role_column_grants',
        '12222': 'routine_privileges',
        '12226': 'role_routine_grants',
        '12229': 'routines',
        '12233': 'schemata',
        '12236': 'sequences',
        '12240': 'sql_features',
        '12242': 'pg_toast_12239',
        '12245': 'sql_implementation_info',
        '12247': 'pg_toast_12244',
        '12250': 'sql_languages',
        '12252': 'pg_toast_12249',
        '12255': 'sql_packages',
        '12257': 'pg_toast_12254',
        '12260': 'sql_parts',
        '12262': 'pg_toast_12259',
        '12265': 'sql_sizing',
        '12267': 'pg_toast_12264',
        '12270': 'sql_sizing_profiles',
        '12272': 'pg_toast_12269',
        '12275': 'table_constraints',
        '12279': 'table_privileges',
        '12283': 'role_table_grants',
        '12286': 'tables',
        '12290': 'transforms',
        '12294': 'triggered_update_columns',
        '12298': 'triggers',
        '12302': 'udt_privileges',
        '12306': 'role_udt_grants',
        '12309': 'usage_privileges',
        '12313': 'role_usage_grants',
        '12316': 'user_defined_types',
        '12320': 'view_column_usage',
        '12324': 'view_routine_usage',
        '12328': 'view_table_usage',
        '12332': 'views',
        '12336': 'data_type_privileges',
        '12340': 'element_types',
        '12344': '_pg_foreign_table_columns',
        '12348': 'column_options',
        '12351': '_pg_foreign_data_wrappers',
        '12354': 'foreign_data_wrapper_options',
        '12357': 'foreign_data_wrappers',
        '12360': '_pg_foreign_servers',
        '12364': 'foreign_server_options',
        '12367': 'foreign_servers',
        '12370': '_pg_foreign_tables',
        '12374': 'foreign_table_options',
        '12377': 'foreign_tables',
        '12380': '_pg_user_mappings',
        '12384': 'user_mapping_options',
        '12388': 'user_mappings',
        '24626': '_level2emissions_20200529',
        '24627': 'level2emissions_20200529',
        '24629': 'pg_toast_24625',
        '24632': '_level2emissions_20200630',
        '24633': 'level2emissions_20200630',
        '24635': 'pg_toast_24631',
        '24672': '_may',
        '24673': 'may',
        '24675': 'pg_toast_24671',
        '24678': '_june',
        '24679': 'june',
        '24681': 'pg_toast_24677',
    }
