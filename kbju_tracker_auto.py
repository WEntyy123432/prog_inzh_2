
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class NutritionRecord:
    calories: float = 0
    proteins: float = 0
    fats: float = 0
    carbs: float = 0


@dataclass
class Person:
    gender: str
    age: int
    height: float
    weight: float
    activity: float


class CalorieCalculator:
    @staticmethod
    def calculate_tdee(person: Person) -> float:
        if person.gender == "Мужчина":
            bmr = 10 * person.weight + 6.25 * person.height - 5 * person.age + 5
        else:
            bmr = 10 * person.weight + 6.25 * person.height - 5 * person.age - 161
        return bmr * person.activity


class MacroCalculator:
    @staticmethod
    def calculate(calories: float) -> NutritionRecord:
        proteins = calories * 0.30 / 4
        fats = calories * 0.30 / 9
        carbs = calories * 0.40 / 4
        return NutritionRecord(calories, proteins, fats, carbs)


class Meal(ABC):
    def __init__(self, name):
        self.name = name
        self.record = NutritionRecord()

    @abstractmethod
    def get_share(self):
        pass


class Breakfast(Meal):
    def __init__(self):
        super().__init__("Завтрак")

    def get_share(self):
        return 0.30


class Lunch(Meal):
    def __init__(self):
        super().__init__("Обед")

    def get_share(self):
        return 0.40


class Dinner(Meal):
    def __init__(self):
        super().__init__("Ужин")

    def get_share(self):
        return 0.30


class NutritionRepository:
    def __init__(self):
        self.meals = [Breakfast(), Lunch(), Dinner()]

    def total(self):
        result = NutritionRecord()
        for meal in self.meals:
            result.calories += meal.record.calories
            result.proteins += meal.record.proteins
            result.fats += meal.record.fats
            result.carbs += meal.record.carbs
        return result


class NutritionService:
    def __init__(self, repository):
        self.repository = repository

    def remaining(self, norm: NutritionRecord):
        total = self.repository.total()
        return NutritionRecord(
            norm.calories - total.calories,
            norm.proteins - total.proteins,
            norm.fats - total.fats,
            norm.carbs - total.carbs
        )


class MainWindow:
    def __init__(self):
        self.repo = NutritionRepository()
        self.service = NutritionService(self.repo)

        self.root = tk.Tk()
        self.root.title("КБЖУ Трекер")
        self.root.geometry("850x700")

        self.create_profile_block()
        self.create_meals_block()

        ttk.Button(self.root, text="Рассчитать", command=self.calculate).pack(pady=10)

        self.output = tk.Text(self.root, height=18)
        self.output.pack(fill="both", expand=True, padx=10, pady=10)

    def create_profile_block(self):
        frame = ttk.LabelFrame(self.root, text="Данные пользователя")
        frame.pack(fill="x", padx=10, pady=5)

        self.gender = tk.StringVar(value="Мужчина")
        self.age = tk.StringVar()
        self.height = tk.StringVar()
        self.weight = tk.StringVar()

        ttk.Label(frame, text="Пол").grid(row=0, column=0)
        ttk.Combobox(frame, textvariable=self.gender,
                     values=["Мужчина", "Женщина"],
                     state="readonly").grid(row=1, column=0)

        ttk.Label(frame, text="Возраст").grid(row=0, column=1)
        ttk.Entry(frame, textvariable=self.age).grid(row=1, column=1)

        ttk.Label(frame, text="Рост").grid(row=0, column=2)
        ttk.Entry(frame, textvariable=self.height).grid(row=1, column=2)

        ttk.Label(frame, text="Вес").grid(row=0, column=3)
        ttk.Entry(frame, textvariable=self.weight).grid(row=1, column=3)

        ttk.Label(frame, text="Активность").grid(row=0, column=4)

        self.activity = ttk.Combobox(
            frame,
            state="readonly",
            values=[
                "1.2 Минимальная",
                "1.375 Низкая",
                "1.55 Средняя",
                "1.725 Высокая",
                "1.9 Очень высокая"
            ]
        )
        self.activity.current(2)
        self.activity.grid(row=1, column=4)

    def create_meals_block(self):
        self.entries = {}

        for meal in self.repo.meals:
            frame = ttk.LabelFrame(self.root, text=meal.name)
            frame.pack(fill="x", padx=10, pady=5)

            labels = ["Калории", "Белки", "Жиры", "Углеводы"]
            fields = {}

            for i, label in enumerate(labels):
                ttk.Label(frame, text=label).grid(row=0, column=i)
                e = ttk.Entry(frame, width=12)
                e.grid(row=1, column=i)
                fields[label] = e

            self.entries[meal.name] = fields

    def calculate(self):
        try:
            person = Person(
                self.gender.get(),
                int(self.age.get()),
                float(self.height.get()),
                float(self.weight.get()),
                float(self.activity.get().split()[0])
            )

            norm_calories = CalorieCalculator.calculate_tdee(person)
            norm = MacroCalculator.calculate(norm_calories)

            for meal in self.repo.meals:
                fields = self.entries[meal.name]

                meal.record = NutritionRecord(
                    float(fields["Калории"].get() or 0),
                    float(fields["Белки"].get() or 0),
                    float(fields["Жиры"].get() or 0),
                    float(fields["Углеводы"].get() or 0)
                )

            total = self.repo.total()
            remain = self.service.remaining(norm)

            text = f"СУТОЧНАЯ НОРМА\n"
            text += f"Калории: {norm.calories:.0f}\n"
            text += f"Белки: {norm.proteins:.1f} г\n"
            text += f"Жиры: {norm.fats:.1f} г\n"
            text += f"Углеводы: {norm.carbs:.1f} г\n\n"

            text += "СЪЕДЕНО\n"
            text += f"Калории: {total.calories:.0f}\n"
            text += f"Белки: {total.proteins:.1f} г\n"
            text += f"Жиры: {total.fats:.1f} г\n"
            text += f"Углеводы: {total.carbs:.1f} г\n\n"

            text += "ОСТАЛОСЬ\n"
            text += f"Калории: {remain.calories:.0f}\n"
            text += f"Белки: {remain.proteins:.1f} г\n"
            text += f"Жиры: {remain.fats:.1f} г\n"
            text += f"Углеводы: {remain.carbs:.1f} г\n"

            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, text)

        except Exception:
            messagebox.showerror("Ошибка", "Проверьте корректность введённых данных.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MainWindow().run()
