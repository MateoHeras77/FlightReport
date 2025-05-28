# Database Schema

## `FlightReport` Table

This table stores the flight report data submitted through the application.

| Column Name              | Data Type (PostgreSQL)   | Description                                                                 | Example Value (from form or typical)         |
|--------------------------|--------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| `id`                     | `BIGINT` (Primary Key)   | Auto-incrementing primary key.                                              | `1`                                          |
| `created_at`             | `TIMESTAMP WITH TIME ZONE` | Timestamp of when the record was created (automatically managed by Supabase). | `2023-10-27T10:30:00Z`                       |
| `flight_date`            | `DATE`                   | Date of the flight.                                                         | `2023-11-15`                                 |
| `origin`                 | `TEXT`                   | Origin airport code (fixed to "YYZ" in the form).                           | `YYZ`                                        |
| `destination`            | `TEXT`                   | Destination airport code.                                                   | `BOG`                                        |
| `flight_number`          | `TEXT`                   | Flight number (e.g., AV205).                                                | `AV205`                                      |
| `std`                    | `TIME`                   | Scheduled Time of Departure.                                                | `23:50:00`                                   |
| `atd`                    | `TIME`                   | Actual Time of Departure.                                                   | `23:55:00`                                   |
| `groomers_in`            | `TIME`                   | Time when groomers entered the aircraft.                                    | `22:30:00`                                   |
| `groomers_out`           | `TIME`                   | Time when groomers exited the aircraft.                                     | `22:45:00`                                   |
| `crew_at_gate`           | `TIME`                   | Time when the crew arrived at the gate.                                     | `23:00:00`                                   |
| `ok_to_board`            | `TIME`                   | Time when it was okay to start boarding.                                    | `23:10:00`                                   |
| `flight_secure`          | `TIME`                   | Time when the flight was secured.                                           | `23:40:00`                                   |
| `cierre_de_puerta`       | `TIME`                   | Time when aircraft doors were closed.                                       | `23:45:00`                                   |
| `push_back`              | `TIME`                   | Time of push back from the gate.                                            | `23:52:00`                                   |
| `pax_ob_total`           | `INTEGER`                | Total number of passengers on board.                                        | `150`                                        |
| `pax_c`                  | `INTEGER`                | Number of passengers in Business Class (Clase C).                           | `10`                                         |
| `pax_y`                  | `INTEGER`                | Number of passengers in Economy Class (Clase Y).                            | `140`                                        |
| `infants`                | `INTEGER`                | Number of infants on board.                                                 | `5`                                          |
| `customs_in`             | `TEXT`                   | Time when customs process started (can also be "No Customs").             | `No Customs` or `10:00:00`                   |
| `customs_out`            | `TEXT`                   | Time when customs process ended (can also be "No Customs").               | `No Customs` or `10:15:00`                   |
| `delay`                  | `TEXT`                   | Delay in minutes, or text like ">200 Escribir en comentarios".             | `30` or `>200 Escribir en comentarios`     |
| `delay_code`             | `TEXT`                   | Codes associated with the delay.                                            | `ATC123`                                     |
| `gate`                   | `TEXT`                   | Departure gate number.                                                      | `F65`                                        |
| `carrousel`              | `TEXT`                   | Baggage claim carrousel number.                                             | `5`                                          |
| `wchr_previous_flight`   | `TEXT`                   | Wheelchair service summary for the previous (arriving) flight.              | `05 WCHR \| 02 WCHC`                         |
| `agents_previous_flight` | `TEXT`                   | Number of agents for the previous (arriving) flight, or text for >20.     | `10` or `> 20 Escribir en comentarios`       |
| `wchr_current_flight`    | `TEXT`                   | Wheelchair service summary for the current (departing) flight.              | `10 WCHR \| 01 WCHC`                         |
| `agents_current_flight`  | `TEXT`                   | Number of agents for the current (departing) flight, or text for >20.       | `12` or `> 20 Escribir en comentarios`       |
| `comments`               | `TEXT`                   | General comments about the flight.                                          | `Boarding started late due to weather.`      |
| `gate_bag`               | `TEXT`                   | Information regarding gate bag status or issues.                            | `Faltan boarding pass`                       |
