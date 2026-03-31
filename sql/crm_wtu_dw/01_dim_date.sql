-- ============================================
-- dim_date — Conformed Date Dimension
-- Covers: 2020-01-01 to 2030-12-31
-- Thai Education Year: starts June (ปีการศึกษา)
-- ============================================

DROP TABLE IF EXISTS dim_date CASCADE;

CREATE TABLE dim_date (
    date_key            INT PRIMARY KEY,            -- YYYYMMDD format
    full_date           DATE NOT NULL UNIQUE,

    -- Calendar attributes
    day_of_week         SMALLINT NOT NULL,           -- 1=Mon, 7=Sun (ISO)
    day_name            VARCHAR(10) NOT NULL,        -- Monday, Tuesday...
    day_name_th         VARCHAR(20) NOT NULL,        -- จันทร์, อังคาร...
    day_of_month        SMALLINT NOT NULL,
    day_of_year         SMALLINT NOT NULL,

    week_of_year        SMALLINT NOT NULL,           -- ISO week
    month_number        SMALLINT NOT NULL,
    month_name          VARCHAR(10) NOT NULL,
    month_name_th       VARCHAR(20) NOT NULL,        -- มกราคม, กุมภาพันธ์...
    quarter             SMALLINT NOT NULL,
    quarter_name        VARCHAR(2) NOT NULL,         -- Q1, Q2, Q3, Q4
    year                SMALLINT NOT NULL,
    year_month          VARCHAR(7) NOT NULL,         -- 2026-03
    year_quarter        VARCHAR(7) NOT NULL,         -- 2026-Q1

    is_weekend          BOOLEAN NOT NULL DEFAULT FALSE,
    is_thai_holiday     BOOLEAN NOT NULL DEFAULT FALSE,
    thai_holiday_name   VARCHAR(100),

    -- Thai Education Calendar
    education_year      SMALLINT NOT NULL,           -- ปีการศึกษา (June start)
    education_sem       SMALLINT NOT NULL,           -- 1=Jun-Oct, 2=Nov-Mar, 3=Apr-May (summer)
    education_year_sem  VARCHAR(10) NOT NULL,        -- "2569/1"

    -- Buddhist Era
    year_be             SMALLINT NOT NULL,           -- พ.ศ.

    -- Enrollment season flags
    is_main_enrollment_period   BOOLEAN NOT NULL DEFAULT FALSE,  -- มี.ค.-มิ.ย.
    is_midyear_enrollment       BOOLEAN NOT NULL DEFAULT FALSE   -- ต.ค.-พ.ย.
);

-- Populate dim_date
INSERT INTO dim_date
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT AS date_key,
    d AS full_date,

    EXTRACT(ISODOW FROM d)::SMALLINT AS day_of_week,
    TO_CHAR(d, 'Day') AS day_name,
    CASE EXTRACT(ISODOW FROM d)::INT
        WHEN 1 THEN 'จันทร์' WHEN 2 THEN 'อังคาร' WHEN 3 THEN 'พุธ'
        WHEN 4 THEN 'พฤหัสบดี' WHEN 5 THEN 'ศุกร์' WHEN 6 THEN 'เสาร์'
        WHEN 7 THEN 'อาทิตย์'
    END AS day_name_th,
    EXTRACT(DAY FROM d)::SMALLINT AS day_of_month,
    EXTRACT(DOY FROM d)::SMALLINT AS day_of_year,

    EXTRACT(WEEK FROM d)::SMALLINT AS week_of_year,
    EXTRACT(MONTH FROM d)::SMALLINT AS month_number,
    TO_CHAR(d, 'Month') AS month_name,
    CASE EXTRACT(MONTH FROM d)::INT
        WHEN 1 THEN 'มกราคม' WHEN 2 THEN 'กุมภาพันธ์' WHEN 3 THEN 'มีนาคม'
        WHEN 4 THEN 'เมษายน' WHEN 5 THEN 'พฤษภาคม' WHEN 6 THEN 'มิถุนายน'
        WHEN 7 THEN 'กรกฎาคม' WHEN 8 THEN 'สิงหาคม' WHEN 9 THEN 'กันยายน'
        WHEN 10 THEN 'ตุลาคม' WHEN 11 THEN 'พฤศจิกายน' WHEN 12 THEN 'ธันวาคม'
    END AS month_name_th,
    EXTRACT(QUARTER FROM d)::SMALLINT AS quarter,
    'Q' || EXTRACT(QUARTER FROM d)::TEXT AS quarter_name,
    EXTRACT(YEAR FROM d)::SMALLINT AS year,
    TO_CHAR(d, 'YYYY-MM') AS year_month,
    EXTRACT(YEAR FROM d)::TEXT || '-Q' || EXTRACT(QUARTER FROM d)::TEXT AS year_quarter,

    EXTRACT(ISODOW FROM d) IN (6, 7) AS is_weekend,
    FALSE AS is_thai_holiday,
    NULL AS thai_holiday_name,

    -- Thai education year: June = start of new year
    CASE
        WHEN EXTRACT(MONTH FROM d) >= 6 THEN EXTRACT(YEAR FROM d)::SMALLINT + 543
        ELSE EXTRACT(YEAR FROM d)::SMALLINT + 542
    END AS education_year,
    -- Semester: 1=Jun-Oct, 2=Nov-Mar, 3=Apr-May (summer)
    CASE
        WHEN EXTRACT(MONTH FROM d) BETWEEN 6 AND 10 THEN 1
        WHEN EXTRACT(MONTH FROM d) >= 11 OR EXTRACT(MONTH FROM d) <= 3 THEN 2
        ELSE 3  -- Apr-May = summer
    END::SMALLINT AS education_sem,
    CASE
        WHEN EXTRACT(MONTH FROM d) >= 6 THEN (EXTRACT(YEAR FROM d)::INT + 543)::TEXT || '/' ||
            CASE WHEN EXTRACT(MONTH FROM d) BETWEEN 6 AND 10 THEN '1' ELSE '2' END
        WHEN EXTRACT(MONTH FROM d) <= 3 THEN (EXTRACT(YEAR FROM d)::INT + 542)::TEXT || '/2'
        ELSE (EXTRACT(YEAR FROM d)::INT + 542)::TEXT || '/3'
    END AS education_year_sem,

    (EXTRACT(YEAR FROM d) + 543)::SMALLINT AS year_be,

    EXTRACT(MONTH FROM d) BETWEEN 3 AND 6 AS is_main_enrollment_period,
    EXTRACT(MONTH FROM d) BETWEEN 10 AND 11 AS is_midyear_enrollment

FROM generate_series('2020-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) AS d;

CREATE INDEX idx_dim_date_full_date ON dim_date (full_date);
CREATE INDEX idx_dim_date_year_month ON dim_date (year, month_number);
CREATE INDEX idx_dim_date_edu_year_sem ON dim_date (education_year, education_sem);

-- Unknown member
INSERT INTO dim_date (date_key, full_date, day_of_week, day_name, day_name_th,
    day_of_month, day_of_year, week_of_year, month_number, month_name, month_name_th,
    quarter, quarter_name, year, year_month, year_quarter, education_year, education_sem,
    education_year_sem, year_be)
VALUES (-1, '1900-01-01', 1, 'Unknown', 'ไม่ทราบ',
    1, 1, 1, 1, 'Unknown', 'ไม่ทราบ',
    1, 'Q0', 1900, '1900-01', '1900-Q0', 2443, 0,
    'N/A', 2443);
