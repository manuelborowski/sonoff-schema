DROP TABLE IF EXISTS sonoff;
DROP TABLE IF EXISTS scheme;

CREATE TABLE sonoff (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sonoff_id TEXT UNIQUE NOT NULL,
      location TEXT default '',
      active INTEGER default 0,
      schemes TEXT default ''
);

CREATE TABLE scheme (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gid INTEGER default 0,
    active INTEGER default 0,
    mon INTEGER default 0,
    tue INTEGER default 0,
    wed INTEGER default 0,
    thu INTEGER default 0,
    fri INTEGER default 0,
    sat INTEGER default 0,
    sun INTEGER default 0,
    on0 TEXT default '',
    off0 TEXT default '',
    on1 TEXT default '',
    off1 TEXT default ''
);