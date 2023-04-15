DROP TABLE IF EXISTS cbVendors;
DROP TABLE IF EXISTS cbProducts;

CREATE TABLE cbVendors(
  id INTEGER PRIMARY KEY,
  razon_social TEXT,
  email TEXT,
  codigo TEXT,
  nro_doc INTEGER
);

CREATE TABLE cbProducts(
  id TEXT PRIMARY KEY,
  nombre TEXT,
  codigo TEXT,
  codigo_barras INTEGER,
  descripcion TEXT,
  precio INTEGER,
  precio_final INTEGER,
  iva REAL,
  rentabilidad REAL,
  costo_interno REAL,
  observaciones TEXT,
  estado TEXT,
  tipo TEXT,
  id_rubro INTEGER,
  id_subrubro INTEGER,
  items TEXT
);


