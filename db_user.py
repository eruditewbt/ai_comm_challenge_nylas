import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# Create the users table
cursor.execute('''
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    grant_id STRING NOT NULL,
    address TEXT
  )
''')

# Create the events table
cursor.execute('''
  CREATE TABLE IF NOT EXISTS scheduled_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    location TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
  )
''')


class DatabaseManager:
    def __init__(self):
        self.connection = sqlite3.connect('example.db')
        self.cursor = self.connection.cursor()

    async def create_user(self, username, email, grant_id, address=None):
        self.cursor.execute('''
            INSERT INTO users (username, email, grant_id, address)
            VALUES (?, ?, ?, ?)
        ''', (username, email, grant_id, address))
        self.connection.commit()
        return {"status": "success", "message": "User created successfully"}

    async def get_user(self, grant_id):
        self.cursor.execute('''
            SELECT * FROM users WHERE grant_id = ?
        ''', (grant_id,))
        return self.cursor.fetchone()

    async def update_user(self, user_id, username, email, grant_id, address=None):
        self.cursor.execute('''
            UPDATE users
            SET username = ?, email = ?, grant_id = ?, address = ?
            WHERE id = ?
        ''', (username, email, grant_id, address, user_id))
        self.connection.commit()
        return {"status": "success", "message": "User updated successfully"}

    async def delete_user(self, user_id):
        self.cursor.execute('''
            DELETE FROM users WHERE id = ?
        ''', (user_id,))
        self.connection.commit()
        return {"status": "success", "message": "User deleted successfully"}

    async def create_event(self, user_id, title, description, start_time, end_time, location=None):
        # Check if the user exists
        self.cursor.execute('''
            SELECT 1 FROM users WHERE id = ?
        ''', (user_id,))
        user_exists = self.cursor.fetchone()

        if not user_exists:
            raise ValueError(f"User with id {user_id} does not exist.")

        # Insert the event for the specific user
        self.cursor.execute('''
            INSERT INTO scheduled_events (user_id, title, description, start_time, end_time, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, start_time, end_time, location))
        self.connection.commit()
        return {"status": "success", "message": "Event created successfully"}

    async def get_event(self, event_id, user_id):
        """
        Retrieve a specific event for a specific user.

        Parameters:
        event_id (int): The ID of the event to retrieve.
        user_id (int): The ID of the user who owns the event.

        Returns:
        tuple: The event data if found, otherwise None.
        """
        self.cursor.execute('''
            SELECT * FROM scheduled_events WHERE id = ? AND user_id = ?
        ''', (event_id, user_id))
        return self.cursor.fetchone()

    async def update_event(self, event_id, user_id, new_event_data):
      """
      Update an event for a specific user.

      Parameters:
      event_id (int): The ID of the event to update.
      user_id (int): The ID of the user who owns the event.
      new_event_data (dict): A dictionary containing the new event data.
                            Example: {'title': 'New Title', 'date': '2023-10-01'}
      """
      # Construct the SET part of the SQL statement dynamically
      set_clause = ', '.join([f"{key} = ?" for key in new_event_data.keys()])
      values = list(new_event_data.values()) + [event_id, user_id]

      self.cursor.execute(f'''
          UPDATE scheduled_events
          SET {set_clause}
          WHERE id = ? AND user_id = ?
      ''', values)
      self.connection.commit()
      return {"status": "success", "message": "Event updated successfully"}


    async def get_events_by_user(self, user_id, limit=10):
        """
        Retrieve a specified number of events for a specific user.

        Parameters:
        user_id (int): The ID of the user whose events to retrieve.
        limit (int): The maximum number of events to retrieve. Default is 10.

        Returns:
        list: A list of event data tuples.
        """
        self.cursor.execute('''
            SELECT * FROM scheduled_events WHERE user_id = ? LIMIT ?
        ''', (user_id, limit))
        return self.cursor.fetchall()
    
    async def count_events_by_user_for_day(self, user_id, date):
      """
      Retrieve the total count of events for a specific user on a specific day.

      Parameters:
      user_id (int): The ID of the user whose events count to retrieve.
      date (str): The date for which to count the events (format: 'YYYY-MM-DD').

      Returns:
      int: The total number of events for the user on the specified date.
      """
      self.cursor.execute('''
          SELECT COUNT(*) FROM scheduled_events 
          WHERE user_id = ? AND DATE(start_time) = ?
      ''', (user_id, date))
      count = self.cursor.fetchone()[0]
      return count
    
    async def get_events_within_date_range(self, user_id, start_date, end_date):
        """
        Retrieve events for a specific user that fall within a specific date range.

        Parameters:
        user_id (int): The ID of the user whose events to retrieve.
        start_date (str): The start date of the range (format: 'YYYY-MM-DD').
        end_date (str): The end date of the range (format: 'YYYY-MM-DD').

        Returns:
        list: A list of events within the specified date range.
        """
        self.cursor.execute('''
            SELECT * FROM scheduled_events 
            WHERE user_id = ? AND start_date >= ? AND end_date <= ?
        ''', (user_id, start_date, end_date))
        events = self.cursor.fetchall()
        return events

    async def delete_events(self, user_id, event_ids):
      """
      Delete a selected list of events for a specific user.

      Parameters:
      user_id (int): The ID of the user whose events to delete.
      event_ids (list): A list of event IDs to delete.

      Returns:
      int: The number of events deleted.
      """
      # Construct the SQL query with placeholders for event IDs
      placeholders = ', '.join(['?'] * len(event_ids))
      query = f'''
          DELETE FROM scheduled_events
          WHERE user_id = ? AND id IN ({placeholders})
      '''
      # Execute the query with user_id and event_ids as parameters
      self.cursor.execute(query, [user_id] + event_ids)
      self.connection.commit()
      return self.cursor.rowcount

    async def close(self):
        self.connection.close()
        return {"status": "success", "message": "Database connection closed"}

conn.commit()
# Commit the changes and close the connection
conn.close()