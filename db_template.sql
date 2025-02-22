CREATE TABLE "BillOfMaterials" (
    "ProductCode" TEXT NOT NULL,
    "ChildProductCode" TEXT NOT NULL,
    "Quantity" INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY("ProductCode", "ChildProductCode")
);

CREATE TABLE "ProductionOrder" (
    "OrderID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "OrderDate" TEXT NOT NULL,
    "ProductCode" TEXT NOT NULL,
    "Quantity" INTEGER NOT NULL DEFAULT 1,
    "Status" TEXT NOT NULL DEFAULT 'Planned'
);

CREATE TABLE "ProductionOrderProgress" (
    "ProgressID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "OrderID" INTEGER NOT NULL,
    "ProductCode" TEXT NOT NULL,
    "QuantityRequired" INTEGER NOT NULL,
    "QuantityCompleted" INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE "Product" (
    "ProductCode" TEXT PRIMARY KEY,
    "Category" TEXT NOT NULL
);

CREATE TABLE "Inventory" (
    "ProductCode" TEXT PRIMARY KEY,
    "QuantityOnHand" INTEGER NOT NULL DEFAULT 0,
    "Locked" INTEGER NOT NULL DEFAULT 0
);