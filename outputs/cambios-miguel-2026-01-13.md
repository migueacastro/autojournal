Aquí tienes el changelog de los commits proporcionados:

# Fecha: 30/12/2025
## Repositorio: frontend.iutepal.sveltekit
 - Se corrigió un error en `/docente/horario` que duplicaba las secciones.
 - Se refactorizó `checkIsProfesorUser` a `redirectUserByGroup` para utilizar los grupos del usuario.
 - Se corrigió el enrutamiento para usuarios que tienen uno de los siguientes grupos: "admin", "administrativo", "docente".
 - Se corrigió la ruta `/login` para mostrar un mensaje de error si el usuario solo tiene el grupo "docente".
## Repositorio: IUTEPAL_REST
 - Se implementaron los grupos de Django en `UserIutepal`.
 - Se añadió el usuario a los grupos al usar funciones como: `create_user`, `create_docente`, `create_superuser`.
 - Se añadió `GroupSerializer` para mostrar los grupos dentro de `UserSerializer`.