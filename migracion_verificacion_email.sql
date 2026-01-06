-- Migración para agregar campos de verificación de email
-- Ejecutar este script en Supabase SQL Editor

-- Agregar columnas de verificación de email a la tabla usuarios
ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS email_verificado BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS token_verificacion VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS fecha_token_verificacion TIMESTAMP;

-- Marcar como verificados a todos los usuarios existentes que no sean USUARIO
UPDATE usuarios 
SET email_verificado = TRUE 
WHERE rol_codigo != 'USUARIO';

-- Marcar como verificados a los usuarios admin existentes
UPDATE usuarios 
SET email_verificado = TRUE, activo = TRUE 
WHERE rol_codigo = 'ADMIN';

-- Comentario en la tabla
COMMENT ON COLUMN usuarios.email_verificado IS 'Indica si el usuario ha verificado su correo electrónico';
COMMENT ON COLUMN usuarios.token_verificacion IS 'Token único para verificación de email';
COMMENT ON COLUMN usuarios.fecha_token_verificacion IS 'Fecha de generación del token de verificación';

-- Mensaje de confirmación
SELECT 'Migración completada exitosamente' AS mensaje;
