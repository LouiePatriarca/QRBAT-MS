from tkinter import messagebox
import customtkinter
import cv2
import PIL
import RPi.GPIO as GPIO

from CTkTable import *
from mlx90614 import MLX90614
from pyzbar.pyzbar import decode
from smbus2 import SMBus
from tkinter import *
from datetime import datetime
from sim800l import SIM800L
from tkinter import ttk
from database import Database

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Based Attendance and Temperature Monitoring System")
        self.root.geometry("1280x1024")

        self.db = Database("/home/sheldoncoopal/QRBAT-MS/qrbat-ms/qrbatms.db")
        self.sim800l=SIM800L('/dev/serial0')
        self.selected_id = 0
        self.student_number = ""
        self.name = ""
        self.parents_contact = ""
        
        self.lbl_qr_code = customtkinter.CTkLabel(self.root, text="", width=1004)
        self.lbl_qr_code.grid(column=0, row=0, padx=10, pady=10)

        self.btn_register = customtkinter.CTkButton(self.root, text="Register Student", command=self.show_registered_students, width=100, height=30)
        self.btn_register.grid(column=0, row=1, padx=10, sticky=NW)

        self.qr_code_detected = False
                           
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("Error", "Could not open camera.")
            return
        
        self.toplevel_window = None
        self.scan_qr_code()
        
    def scan_qr_code(self):
        if self.camera == None:
            self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            self.camera.open(0)

        GPIO.output(17, GPIO.LOW)
        GPIO.output(27, GPIO.LOW)
        ret, frame = self.camera.read()
        if not ret:
            return
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = PIL.Image.fromarray(frame)
        my_image = customtkinter.CTkImage(light_image=image,dark_image=image,size=(1004, 640))
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
                
                # Check if attendance already exists
                if not self.db.attendance_exists(student_number, attendance_date):
                    GPIO.output(17, GPIO.HIGH)
                    self.db.add_attendance(student_number, attendance_date, attendance_time, temperature)
                    name = self.db.get_name_by_number(student_number)
                    self.show_student_information(student_number, name, attendance_date, attendance_time, temperature)
                    self.camera.release()
                else:
                    GPIO.output(27, GPIO.HIGH)
                    self.show_attendance_exists()
                    self.camera.release()

            bus.close()
            student_number = ""
            temperature = "0"
            self.qr_code_detected = False

        if not self.qr_code_detected:
            self.root.after(20, self.scan_qr_code)

    def show_attendance_exists(self):
        show_attendance_exists_window = customtkinter.CTkToplevel()
        show_attendance_exists_window.geometry("1280x1024")
        show_attendance_exists_window.title("Already Logged In")

        name_label = customtkinter.CTkLabel(show_attendance_exists_window, text="You have already logged in!", text_color="red", font=("Arial", 32, "bold"))
        name_label.pack(fill=BOTH, expand=True)
        show_attendance_exists_window.after(3000, lambda: show_attendance_exists_window.destroy())

    def show_student_information(self, student_number, name, attendance_date, attendance_time, temperature):
        student_information_window = customtkinter.CTkToplevel()
        student_information_window.geometry("1280x1024")
        student_information_window.title("Logged In")

        welcome_label = customtkinter.CTkLabel(student_information_window, text="Welcome!", font=("Arial", 32, "bold"))
        welcome_label.pack(fill=BOTH, expand=True)

        name_label = customtkinter.CTkLabel(student_information_window, text=name, text_color="blue", font=("Arial", 80, "bold"))
        name_label.pack(fill=BOTH, expand=True)

        student_number_label = customtkinter.CTkLabel(student_information_window, text=student_number, font=("Arial", 24, "bold"))
        student_number_label.pack(fill=BOTH, expand=True)

        date_label = customtkinter.CTkLabel(student_information_window, text=attendance_date + " " + attendance_time, font=("Arial", 24, "bold"))
        date_label.pack(fill=BOTH, expand=True)

        temperature_color = "red" if float(temperature) > 37 else "green"
        temperature_label = customtkinter.CTkLabel(student_information_window, text="Temperature: " + temperature, text_color=temperature_color, font=("Arial", 24, "bold"))
        temperature_label.pack(fill=BOTH, expand=True)
        student_information_window.after(3000, lambda: student_information_window.destroy())

    def populate_table(self, tree):
        for row in tree.get_children():
            tree.delete(row)
        students = self.db.get_students()
        for student in students:
            tree.insert('', 'end', values=(student[1], student[2], student[3]))

    def show_registered_students(self):
        window_width = 640
        window_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        registered_students_window = customtkinter.CTkToplevel()
        registered_students_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        registered_students_window.title("Student Registration")
        registered_students_window.resizable(False,False)

        tree = ttk.Treeview(registered_students_window, columns=('student_number', 'name', 'parent_contact'), show='headings')
        tree.heading('student_number', text='Student Number')
        tree.heading('name', text='Name')
        tree.heading('parent_contact', text="Parent's Contact")
        tree.grid(column=0, row=0, columnspan=2, sticky=NW, padx=20, pady=20)

        add_button = customtkinter.CTkButton(registered_students_window, text="Add", command=lambda: self.show_registration_form(tree))
        add_button.grid(column=0, row=1, sticky=NW, padx=(20,0), pady=(0,20))

        edit_button = customtkinter.CTkButton(registered_students_window, text="Edit", command=lambda: self.show_edit_student_form(tree))
        edit_button.grid(column=0, row=1, sticky=NW, padx=(170,0), pady=(0,20))

        delete_button = customtkinter.CTkButton(registered_students_window, text="Delete", fg_color="red", command=lambda: self.delete_student(registered_students_window,tree))
        delete_button.grid(column=0, row=1, sticky=NW, padx=(320,0), pady=(0,20))

        self.populate_table(tree)

        def on_select(event):
            selected_item = tree.selection()[0]
            self.student_number = tree.item(selected_item, 'values')[0]
            self.name = tree.item(selected_item, 'values')[1]
            self.parents_contact = tree.item(selected_item, 'values')[2]
            self.selected_id = self.db.get_id_by_student_number(self.student_number)[0]
            print(self.selected_id)

        tree.bind('<<TreeviewSelect>>', on_select)

    def show_registration_form(self, tree):
        registration_tree = tree
        window_width = 350
        window_height = 200
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        registration_window = customtkinter.CTkToplevel()
        registration_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        registration_window.title("Student Registration")
        registration_window.resizable(False,False)

        id_number_label = customtkinter.CTkLabel(registration_window, text="ID Number: ")
        id_number_label.grid(column=0, row=0, sticky=NW, padx=(20,0), pady=(20,10))
        id_number_entry = customtkinter.CTkEntry(registration_window)
        id_number_entry.grid(column=0, row=0, sticky=NW, padx=(170,0), pady=(20,10))

        name_label = customtkinter.CTkLabel(registration_window, text="Name: ")
        name_label.grid(column=0, row=1, sticky=NW, padx=(20,0), pady=(0,10))
        name_entry = customtkinter.CTkEntry(registration_window)
        name_entry.grid(column=0, row=1, sticky=NW, padx=(170,0), pady=(0,10))

        parents_contact_label = customtkinter.CTkLabel(registration_window, text="Parent's Contact: ")
        parents_contact_label.grid(column=0, row=2, sticky=NW, padx=(20,0), pady=(0,10))
        parents_contact_entry = customtkinter.CTkEntry(registration_window)
        parents_contact_entry.grid(column=0, row=2, sticky=NW, padx=(170,0), pady=(0,10))

        register_button = customtkinter.CTkButton(registration_window, text="Register", command=lambda: self.register_student(id_number_entry.get(), name_entry.get(), parents_contact_entry.get(), registration_window, registration_tree))
        register_button.grid(column=0, row=3, sticky=NW, padx=(20,0), pady=(10,10))

        cancel_button = customtkinter.CTkButton(registration_window, text="Cancel", fg_color="red", command=registration_window.destroy)
        cancel_button.grid(column=0, row=3, sticky=NW, padx=(170,0), pady=(10,10))

    def show_edit_student_form(self, tree):
        registration_tree = tree
        window_width = 350
        window_height = 200
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        registration_window = customtkinter.CTkToplevel()
        registration_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        registration_window.title("Student Registration")
        registration_window.resizable(False,False)

        id_number_label = customtkinter.CTkLabel(registration_window, text="ID Number: ")
        id_number_label.grid(column=0, row=0, sticky=NW, padx=(20,0), pady=(20,10))
        id_number_entry = customtkinter.CTkEntry(registration_window)
        id_number_entry.grid(column=0, row=0, sticky=NW, padx=(170,0), pady=(20,10))

        name_label = customtkinter.CTkLabel(registration_window, text="Name: ")
        name_label.grid(column=0, row=1, sticky=NW, padx=(20,0), pady=(0,10))
        name_entry = customtkinter.CTkEntry(registration_window)
        name_entry.grid(column=0, row=1, sticky=NW, padx=(170,0), pady=(0,10))

        parents_contact_label = customtkinter.CTkLabel(registration_window, text="Parent's Contact: ")
        parents_contact_label.grid(column=0, row=2, sticky=NW, padx=(20,0), pady=(0,10))
        parents_contact_entry = customtkinter.CTkEntry(registration_window)
        parents_contact_entry.grid(column=0, row=2, sticky=NW, padx=(170,0), pady=(0,10))

        id_number_entry.insert(0, self.student_number)
        name_entry.insert(0, self.name)
        parents_contact_entry.insert(0, self.parents_contact)

        update_button = customtkinter.CTkButton(registration_window, text="Update", command=lambda: self.update_student(id_number_entry.get(), name_entry.get(), parents_contact_entry.get(), registration_window, tree))
        update_button.grid(column=0, row=3, sticky=NW, padx=(20,0), pady=(10,10))

        cancel_button = customtkinter.CTkButton(registration_window, text="Cancel", fg_color="red", command=registration_window.destroy)
        cancel_button.grid(column=0, row=3, sticky=NW, padx=(170,0), pady=(10,10))
        
    def register_student(self, id_number, name, parent_contact, registration_window, tree):
        try:
            self.db.add_student(id_number, name, parent_contact)
            registration_window.destroy()
            self.populate_table(tree)
            messagebox.showinfo('Registration', 'Student successfully registered!', parent=registration_window)
        except Exception as e:
            messagebox.showinfo('Registration', 'Registration Failed: ' + str(e), parent=registration_window)

    def update_student(self, student_number, name, parent_contact, registration_window, tree):
        try:
            if not self.selected_id == 0:
                self.db.update_student(self.selected_id, student_number, name, parent_contact)
                messagebox.showinfo('Update', 'Student information successfully updated!', parent=registration_window)
                registration_window.destroy()
                self.populate_table(tree)
            else:
                messagebox.showinfo('Update', 'No item selected. Please select an item.', parent=registration_window)
        except Exception as e:
            messagebox.showinfo('Update', 'Update Failed: ' + str(e), parent=registration_window)

    def delete_student(self, registration_window, tree):
        try:
            if not self.selected_id == 0:
                confirm = messagebox.askyesno('Delete Confirmation', 'Are you sure you want to delete this student?', parent=registration_window)
                if confirm:
                    self.db.delete_student(self.selected_id)
                    messagebox.showinfo('Delete', 'Student successfully deleted', parent=registration_window)
                    self.populate_table(tree)
            else:
                messagebox.showinfo('Delete', 'No item selected. Please select an item.', parent=registration_window)
        except Exception as e:
            messagebox.showinfo('Delete', 'Delete Failed: ' + str(e), parent=registration_window)

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