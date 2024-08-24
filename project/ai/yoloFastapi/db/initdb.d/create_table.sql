CREATE TABLE nutritions (
    `id`        INT          NOT NULL ,
    `name`      VARCHAR(25)  NOT NULL UNIQUE,
    `weight`    DECIMAL(6,2) NOT NULL,
    `kcal`      DECIMAL(6,2) NOT NULL,
    `carbonate`     DECIMAL(6,2) NOT NULL,
    `sugar`     DECIMAL(6,2) NOT NULL,
    `fat`       DECIMAL(6,2) NOT NULL,
    `protein`   DECIMAL(6,2) NOT NULL,
    `calcium`   DECIMAL(6,2) NOT NULL,
    `p`         DECIMAL(6,2) NOT NULL,
    `salt`      DECIMAL(6,2) NOT NULL,
    `mg`        DECIMAL(6,2) NOT NULL,
    `iron`      DECIMAL(6,2) NOT NULL,
    `zinc`      DECIMAL(6,2) NOT NULL,
    `cholesterol`      DECIMAL(6,2) NOT NULL,
    `trans`     DECIMAL(6,2) NOT NULL,
    PRIMARY KEY (id)
);