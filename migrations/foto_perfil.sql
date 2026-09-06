-- Execute uma vez no banco MySQL usado pela API, antes de reiniciá-la.
ALTER TABLE empreendedor
    ADD COLUMN foto_perfil MEDIUMBLOB NULL;
