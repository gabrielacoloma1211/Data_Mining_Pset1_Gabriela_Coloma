***Volumetría por tramo***

<img width="1140" height="505" alt="volumetria" src="https://github.com/user-attachments/assets/e3035801-0b6f-4a0a-a5ca-27d9c3ac6fe9" />


***Idempotencia***
Se da porque en el exporter usamos UPSERT, que garantiza que si un registro con la misma clave primaria (id) ya existe en la tabla, no se inserta un duplicado sino que se actualiza el registro existente.

De esta forma:

Si el pipeline se ejecuta dos o más veces con el mismo rango de datos, la cantidad de registros en la tabla no aumenta.

Se evita la duplicación de información.

Siempre se conserva la última versión del payload asociada al mismo id.

Esto asegura que el proceso es idempotente, ya que múltiples ejecuciones producen el mismo estado final en la base de datos.

Datos de la primera corrida con hora:
<img width="1232" height="493" alt="run1" src="https://github.com/user-attachments/assets/5c9a5311-0a26-4dee-befb-d83f3be0f35a" />
<img width="1259" height="671" alt="count1" src="https://github.com/user-attachments/assets/f60e2165-ed69-485a-864b-1f45e9c5815b" />

Datos después de segunda corrida con hora: 
<img width="1244" height="478" alt="run2" src="https://github.com/user-attachments/assets/b60e53b6-27db-426d-816c-3fe51055c4a2" />
<img width="1116" height="827" alt="count2" src="https://github.com/user-attachments/assets/78cfc877-ca1e-4e55-bc75-c0ba90a73eb2" />



Vemos que solo hay uno y no hay duplicados
