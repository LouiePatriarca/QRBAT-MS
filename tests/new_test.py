import customtkinter
import cv2
import PIL
import RPi.GPIO as GPIO
import sqlite3
import time
import threading

from CTkTable import *
from mlx90614 import MLX90614
from pyzbar.pyzbar import decode
from smbus2 import SMBus
from tkinter import *
from datetime import datetime
from sim800l import SIM800L
from tkinter import ttk
from tkinter import messagebox

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

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

    def update_data(self, tree, student_number, name, parent_contact):
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning('Warning', 'Please select a record to update')
            return
        data = tree.item(selected_item)
        item_id = data['values'][0]
        number = student_number.get()
        student_name = name.get()
        parent_contact = parent_contact.get()
        
        self.update_student(item_id, number, student_name, parent_contact)
        messagebox.showinfo('Success', 'Data updated successfully')

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Based Attendance and Temperature Monitoring System")
        self.root.geometry("1280x1024")

        self.db = Database("/home/sheldoncoopal/QRBAT-MS/qrbat-ms/qrbatms.db")
        self.sim800l=SIM800L('/dev/serial0')
        
        self.top_frame = customtkinter.CTkFrame(self.root,corner_radius=0)
        self.top_frame.pack(fill=BOTH, expand=True)

        self.lbl_qr_code = customtkinter.CTkLabel(self.top_frame, text="")
        self.lbl_qr_code.pack(fill=BOTH, expand=True)

        self.top_frame.pack_propagate(False) 
        
        self.bottom_frame = customtkinter.CTkFrame(self.root,corner_radius=0, height=100)
        self.bottom_frame.pack(side=BOTTOM, fill=X)

        self.btn_register = customtkinter.CTkButton(self.bottom_frame, text="Register Student", command=self.show_registration_form, width=100, height=30)
        self.btn_register.place(in_=self.bottom_frame, relx=0.5, rely=0.5, anchor=CENTER)

        self.bottom_frame.pack_propagate(False) 
        self.qr_code_detected = False
                           
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("Error", "Could not open camera.")
            return
        
        self.scan_qr_code()
       
    def scan_qr_code(self):
        thread = None
        GPIO.output(17, GPIO.LOW)
        GPIO.output(27, GPIO.LOW)
        ret, frame = self.camera.read()
        if not ret:
            return
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = PIL.Image.fromarray(frame)
        my_image = customtkinter.CTkImage(light_image=image,dark_image=image,size=(800, 600))
        self.lbl_qr_code.configure(image=my_image)
        decoded_objects = decode(frame)
        if len(decoded_objects) > 0:
            points = decoded_objects[0].rect
            x, y, w, h = points[0], points[1], points[2], points[3]
            
            # Draw a rectangle around the QR code
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            self.qr_code_detected = True
            bus = SMBus(1) 
            sensor= MLX90614(bus, address=0x5A)
            print("Data:", decoded_objects[0].data.decode('utf-8'))
            print(sensor.get_obj_temp())
            student_number = decoded_objects[0].data.decode('utf-8')
            temperature = "{:.2f}".format(sensor.get_obj_temp())
            if student_number != "" and temperature != "0" and self.qr_code_detected:
                now = datetime.now()
                attendance_date = now.strftime("%d/%m/%Y")
                attendance_time = now.strftime("%H:%M:%S")
                # if self.db.attendance_exists(student_number, attendance_date):
                #     GPIO.output(27, GPIO.HIGH)
                #     # self.show_attendance_exists()
                #     return
                
                GPIO.output(17, GPIO.HIGH)
                name = self.db.get_name_by_number(student_number)
                self.show_student_information(student_number, name, attendance_date, attendance_time, temperature)
                self.db.add_attendance(student_number, attendance_date, attendance_time, temperature)
                # sms= "Student Number: " + student_number + "\n" + "Name: " + name + "\n" + "Time In: " + attendance_date + " " + attendance_time + "\n" + "Temperature: " + temperature 
                # contact_number = self.db.get_parent_contact_by_number(student_number)
                # result = self.sim800l.send_sms(contact_number,sms)
                # print(result)
                bus.close()
                time.sleep(3)
                
            student_number = ""
            temperature = "0"
            decoded_objects.clear()
            self.qr_code_detected = False
            frame = None
            ret = False
            image = None
        else:
            decoded_objects.clear()     


        if not self.qr_code_detected:
            self.root.after(10, self.scan_qr_code)

    def show_attendance_exists(self):
        show_attendance_exists_window = customtkinter.CTkToplevel()
        show_attendance_exists_window.geometry("1280x1024")
        show_attendance_exists_window.title("Already Logged In")

        name_label = customtkinter.CTkLabel(show_attendance_exists_window, text="You have already logged in!", text_color="red", font=("Arial", 32, "bold"))
        name_label.pack(fill=BOTH, expand=True)
        
        show_attendance_exists_window.after(3000, show_attendance_exists_window.destroy())
    
    def show_student_information(self, student_number, name, attendance_date, attendance_time, temperature):
        student_information_window = customtkinter.CTkToplevel()
        student_information_window.geometry("1280x1024")
        student_information_window.title("Logged In")

        name_label = customtkinter.CTkLabel(student_information_window, text=name, text_color="blue", font=("Arial", 32, "bold"))
        name_label.pack(fill=BOTH, expand=True)

        student_number_label = customtkinter.CTkLabel(student_information_window, text=student_number, font=("Arial", 24, "bold"))
        student_number_label.pack(fill=BOTH, expand=True)

        date_label = customtkinter.CTkLabel(student_information_window, text=attendance_date + " " + attendance_time, font=("Arial", 24, "bold"))
        date_label.pack(fill=BOTH, expand=True)

        temperature_color = "red" if float(temperature) > 37 else "green"
        temperature_label = customtkinter.CTkLabel(student_information_window, text="Temperature: " + temperature, text_color=temperature_color, font=("Arial", 24, "bold"))
        temperature_label.pack(fill=BOTH, expand=True)

        student_information_window.after(3000, student_information_window.destroy())

    def populate_table(self, tree):
        for row in tree.get_children():
            tree.delete(row)
        students = self.db.get_students()
        for student in students:
            tree.insert('', 'end', values=(student[1], student[2], student[3]))

    def show_registration_form(self):
        registration_window = customtkinter.CTkToplevel()
        registration_window.geometry("800x600")
        registration_window.title("Student Registration")

        tree = ttk.Treeview(registration_window, columns=('student_number', 'name', 'parent_contact'), show='headings')
        tree.heading('student_number', text='Student Number')
        tree.heading('name', text='Name')
        tree.heading('parent_contact', text="Parent's Contact")
        tree.pack()

        registration_form_frame = customtkinter.CTkFrame(registration_window,corner_radius=0)
        registration_form_frame.pack()

        id_number_label = customtkinter.CTkLabel(registration_form_frame, text="ID Number: ")
        id_number_label.grid(column=0, row=0)
        id_number_entry = customtkinter.CTkEntry(registration_form_frame)
        id_number_entry.grid(column=1, row=0)
        
        name_label = customtkinter.CTkLabel(registration_form_frame, text="Name: ")
        name_label.grid(column=0, row=1)
        name_entry = customtkinter.CTkEntry(registration_form_frame)
        name_entry.grid(column=1, row=1)
        
        parents_contact_label = customtkinter.CTkLabel(registration_form_frame, text="Parent's Contact: ")
        parents_contact_label.grid(column=0, row=2)
        parents_contact_entry = customtkinter.CTkEntry(registration_form_frame)
        parents_contact_entry.grid(column=1, row=2)

        register_button = customtkinter.CTkButton(registration_form_frame, text="Submit", command=lambda: self.db.add_student(id_number_entry.get(), name_entry.get(), parents_contact_entry.get()))
        register_button.grid(column=1, row=3)
                           
        self.populate_table(tree)
        
    def __del__(self):
        if self.camera.isOpened():
            self.camera.release()
        
if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(17, GPIO.OUT)
    GPIO.setup(27, GPIO.OUT)
    
    root = customtkinter.CTk()
    app = MainApp(root)
    root.mainloop()
