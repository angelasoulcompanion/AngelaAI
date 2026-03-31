-- ============================================
-- CRM WTU Data Warehouse — Database Creation
-- Target: PostgreSQL @ pgsql02.xtrathai.local
-- Source: crm_wtu (public schema)
-- Author: Angela DW Architect
-- Date: 2026-03-30
-- ============================================

-- Run as superuser/admin on pgsql02
CREATE DATABASE crm_wtu_dw
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

COMMENT ON DATABASE crm_wtu_dw IS 'Data Warehouse for CRM WTU — Student Recruitment Pipeline Analytics';

-- After creating DB, connect to crm_wtu_dw and run remaining scripts
