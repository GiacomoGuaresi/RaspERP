CREATE TABLE "BillOfMaterials" (
    "BillOfMaterialID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "ProductCode" TEXT NOT NULL,
    "ChildProductCode" TEXT NOT NULL,
    "Quantity" INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE "ProductionOrder" (
    "OrderID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "OrderDate" TEXT NOT NULL,
    "ProductCode" TEXT NOT NULL,
    "Quantity" INTEGER NOT NULL DEFAULT 1,
    "QuantityCompleted" INTEGER NOT NULL DEFAULT 0,
    "Status" TEXT NOT NULL DEFAULT 'Planned',
    "ParentOrderID" INTEGER,
    "AssignedUser"	TEXT
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
    "Category" TEXT NOT NULL,
    "Metadata" TEXT NOT NULL DEFAULT "{}",
    "Image" TEXT
);

CREATE TABLE "Inventory" (
    "ProductCode" TEXT PRIMARY KEY,
    "QuantityOnHand" INTEGER NOT NULL DEFAULT 0,
    "Locked" INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE "Logs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "message" TEXT NOT NULL,
    "user" TEXT
);

CREATE TABLE "Metadata" (
    "MetadataCode" TEXT PRIMARY KEY,
    "Category" TEXT
);

CREATE TABLE "User" (
    "Username" TEXT PRIMARY KEY,
    "Email" TEXT,
    "Password" TEXT,
    "DashboardJson" TEXT DEFAULT "{}"
);