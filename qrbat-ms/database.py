import sqlite3
from tkinter import messagebox


class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cur.execute('''CREATE TABLE IF NOT EXISTS students
                            (id INTEGER PRIMARY KEY, student_number TEXT, name TEXT, parent_contact TEXT)''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS attendance
                            (id INTEGER PRIMARY KEY, student_number INTEGER, date TEXT, time TEXT, temperature REAL, status TEXT)''')
        self.conn.commit()

    # Attendance 
    def attendance_exists(self, student_number, date):
        self.cur.execute("SELECT * FROM attendance WHERE student_number=? AND date=?", (student_number, date))
        return self.cur.fetchone()

    def add_attendance(self, student_number, date, time, temperature):
        self.cur.execute("INSERT INTO attendance (student_number, date, time, temperature) VALUES (?, ?, ?, ?)",
                        (student_number, date, time, temperature))
        self.conn.commit()

    # Student
    def get_students(self):
        self.cur.execute("SELECT * FROM students")
        return self.cur.fetchall()

    def get_student_by_number(self, student_number):
        self.cur.execute("SELECT * FROM students WHERE student_number=?", (student_number,))
        return self.cur.fetchone()
    
    def get_id_by_student_number(self, student_number):
        self.cur.execute("SELECT id FROM students WHERE student_number=?", (student_number,))
        return self.cur.fetchone()
    
    def get_name_by_number(self, student_number):
        self.cur.execute("SELECT name FROM students WHERE student_number=?", (student_number,))
        student = self.cur.fetchone()
        return student[0]
    
    def get_parent_contact_by_number(self, student_number):
        self.cur.execute("SELECT parent_contact FROM students WHERE student_number=?", (student_number,))
        student = self.cur.fetchone()
        return student[0]

    def add_student(self, student_number, name, parent_contact):
        self.cur.execute("INSERT INTO students (student_number, name, parent_contact) VALUES (?, ?, ?)",
                         (student_number, name, parent_contact))
        self.conn.commit()

    def delete_student(self, selected_id):
        self.cur.execute('DELETE FROM students WHERE id=?', (selected_id,))
        self.conn.commit()

    def delete_data(self, tree):
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning('Warning', 'Please select a record to delete')
            return
        data = tree.item(selected_item)
        item_id = data['values'][0]
        self.delete_student(item_id)
        messagebox.showinfo('Success', 'Data deleted successfully')

    def update_student(self, selected_id, student_number, name, parent_contact):
        self.cur.execute('UPDATE students SET student_number=?, name=?, parent_contact=? WHERE id=?', (student_number, name, parent_contact, selected_id))
        self.conn.commit()
