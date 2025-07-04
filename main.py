import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import wikipediaapi
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import socket
import dns.resolver
import csv
import pandas as pd
import random
import os
import webbrowser
import json
from datetime import datetime
import re

try:
    import whois
except ImportError:
    whois = None


class WikiDomainChecker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WikiLink Domain Checker Enhanced")
        self.root.geometry("800x700")  # Увеличил размер окна
        self.root.resizable(False, False)

        self.results = []
        self.all_checked_domains = []
        self.is_running = False
        self.stop_requested = False
        self.setup_ui()

    def save_csv(self):
        print("Вызван метод save_csv")
        if not self.all_checked_domains:
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Ключевое слово", "Статья", "Ссылка", "Домен", "Статус",
                        "Архив", "Количество снимков", "Дата проверки",
                        "Заголовок страницы", "Превью текста"
                    ])
                    writer.writerows(self.all_checked_domains)
                messagebox.showinfo("Успех", f"Сохранено {len(self.all_checked_domains)} записей в: {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def save_excel(self):
        print("Вызван метод save_excel")
        if not self.all_checked_domains:
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )

        if filepath:
            try:
                df = pd.DataFrame(self.all_checked_domains,
                                  columns=[
                                      "Ключевое слово", "Статья", "Ссылка", "Домен", "Статус",
                                      "Архив", "Количество снимков", "Дата проверки",
                                      "Заголовок страницы", "Превью текста"
                                  ])
                df.to_excel(filepath, index=False)
                messagebox.showinfo("Успех", f"Сохранено {len(self.all_checked_domains)} записей в: {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def open_contact(self):
        print("Вызван метод open_contact")
        webbrowser.open("https://t.me/Userspoi")

    def setup_ui(self):
        print("Начинаю создание интерфейса...")

        # Заголовок
        title_label = tk.Label(self.root, text="WikiLink Domain Checker Enhanced",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Поле ввода ключевых слов
        tk.Label(self.root, text="Ключевые слова (через запятую):").pack(pady=5)
        self.keywords_entry = tk.Entry(self.root, width=60)
        self.keywords_entry.pack(pady=5)

        # Выбор языка
        lang_frame = tk.Frame(self.root)
        lang_frame.pack(pady=5)
        tk.Label(lang_frame, text="Язык Wikipedia:").pack(side='left', padx=5)
        self.lang_var = tk.StringVar(value="ru")
        lang_options = [("Русский", "ru"), ("English", "en"), ("Deutsch", "de"), ("Français", "fr")]
        for text, value in lang_options:
            tk.Radiobutton(lang_frame, text=text, variable=self.lang_var,
                           value=value).pack(side='left', padx=5)

        # Настройки извлечения контента
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=5)

        self.extract_content_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Извлекать содержимое страниц",
                       variable=self.extract_content_var).pack(side='left', padx=5)

        self.check_snapshots_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Проверять количество снимков",
                       variable=self.check_snapshots_var).pack(side='left', padx=5)

        # Кнопки управления
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        self.start_button = tk.Button(control_frame, text="Начать проверку",
                                      command=self.start_check, bg="#4CAF50",
                                      fg="white", font=("Arial", 10, "bold"))
        self.start_button.pack(side='left', padx=5)

        self.stop_button = tk.Button(control_frame, text="Стоп",
                                     command=self.stop_check, bg="#f44336",
                                     fg="white", font=("Arial", 10, "bold"), state='disabled')
        self.stop_button.pack(side='left', padx=5)

        # Прогресс бар
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(pady=5, padx=20, fill='x')

        # Статус
        self.status_label = tk.Label(self.root, text="Готов к работе", fg="green")
        self.status_label.pack(pady=5)

        # Лог
        tk.Label(self.root, text="Лог:").pack(pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(self.root, height=10, width=80)
        self.log_text.pack(pady=5, padx=20, fill='both', expand=True)

        # Кнопки сохранения
        save_frame = tk.Frame(self.root, bg="lightgray", relief="raised", bd=2)
        save_frame.pack(pady=10, padx=10, fill='x')

        save_label = tk.Label(save_frame, text="Сохранение результатов:",
                              font=("Arial", 10, "bold"), bg="lightgray")
        save_label.pack(pady=5)

        buttons_frame = tk.Frame(save_frame, bg="lightgray")
        buttons_frame.pack(pady=5)

        self.save_csv_button = tk.Button(buttons_frame, text="💾 Сохранить CSV",
                                         command=self.save_csv,
                                         bg="#FF5722", fg="white",
                                         font=("Arial", 10, "bold"),
                                         width=15, height=2)
        self.save_csv_button.pack(side='left', padx=10)

        self.save_excel_button = tk.Button(buttons_frame, text="📊 Сохранить Excel",
                                           command=self.save_excel,
                                           bg="#4CAF50", fg="white",
                                           font=("Arial", 10, "bold"),
                                           width=15, height=2)
        self.save_excel_button.pack(side='left', padx=10)

        self.contact_button = tk.Button(buttons_frame, text="📞 Связь",
                                        command=self.open_contact,
                                        bg="#2196F3", fg="white",
                                        font=("Arial", 10, "bold"),
                                        width=15, height=2)
        self.contact_button.pack(side='left', padx=10)

        # Добавляем тестовые данные
        self.all_checked_domains = []
        self.log("Программа готова к работе!")

    def log(self, message):
        if hasattr(self, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.root.update()
        else:
            print(message)

    def start_check(self):
        if self.is_running:
            return

        keywords_text = self.keywords_entry.get().strip()
        if not keywords_text:
            messagebox.showerror("Ошибка", "Введите ключевые слова")
            return

        keywords = [kw.strip() for kw in keywords_text.split(',')]
        language = self.lang_var.get()

        self.is_running = True
        self.stop_requested = False
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress.start()
        self.status_label.config(text="Проверка...", fg="orange")
        self.log_text.delete(1.0, tk.END)
        self.results = []
        self.all_checked_domains = []

        thread = threading.Thread(target=self.check_domains, args=(keywords, language))
        thread.start()

    def stop_check(self):
        self.stop_requested = True
        self.log("Остановка проверки...")

    def extract_page_content(self, url):
        """Извлекает содержимое страницы: заголовок, описание, текст"""
        try:
            self.log(f"    Извлекаем содержимое страницы...")
            headers = {
                "User-Agent": "WikiLinkChecker/1.0 (https://example.com/contact)"
            }
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return "Заголовок недоступен", "Содержимое недоступно"

            soup = BeautifulSoup(response.text, 'html.parser')

            # Извлекаем заголовок
            title = "Заголовок не найден"
            if soup.title:
                title = soup.title.get_text().strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()

            # Извлекаем описание и текст
            description = ""

            # Пытаемся найти meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content'].strip()

            # Если нет meta description, берем текст из параграфов
            if not description:
                paragraphs = soup.find_all('p')
                texts = []
                for p in paragraphs[:3]:  # Берем первые 3 параграфа
                    text = p.get_text().strip()
                    if text and len(text) > 20:  # Игнорируем короткие фрагменты
                        texts.append(text)

                if texts:
                    description = ' '.join(texts)

            # Ограничиваем длину описания
            if len(description) > 1000:
                description = description[:1000] + "..."

            # Очищаем текст от лишних символов
            description = re.sub(r'\s+', ' ', description).strip()
            title = re.sub(r'\s+', ' ', title).strip()

            if not description:
                description = "Содержимое не найдено"

            self.log(f"    ✓ Заголовок: {title[:50]}...")
            self.log(f"    ✓ Превью: {description[:100]}...")

            return title, description

        except Exception as e:
            self.log(f"    ⚠ Ошибка извлечения содержимого: {e}")
            return "Ошибка извлечения заголовка", "Ошибка извлечения содержимого"

    def get_archive_snapshots_count(self, domain):
        """Получает количество снимков в Archive.org через CDX API"""
        try:
            self.log(f"    Получаем количество снимков для {domain}")
            # Используем CDX API для получения количества снимков
            url = f"https://web.archive.org/cdx/search/cdx?url={domain}&showNumPages=true"
            headers = {"User-Agent": "WikiLinkChecker/1.0"}

            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                self.log(f"    CDX API недоступен (код {response.status_code})")
                return 0

            # Пробуем получить количество через showNumPages
            text = response.text.strip()
            if text.isdigit():
                count = int(text)
                self.log(f"    ✓ Найдено {count} снимков")
                return count

            # Если showNumPages не работает, считаем строки
            lines = text.split('\n')
            count = len([line for line in lines if line.strip()])
            self.log(f"    ✓ Найдено {count} снимков")
            return count

        except Exception as e:
            self.log(f"    ⚠ Ошибка получения количества снимков: {e}")
            return 0

    def check_domains(self, keywords, language):
        try:
            if self.stop_requested:
                return

            self.log(f"Поиск страниц Wikipedia ({language})...")
            pages = self.search_wikipedia(keywords, language)

            if not pages:
                self.log("Страницы не найдены")
                self.finish_check()
                return

            self.log(f"Найдено {len(pages)} страниц")

            for keyword, title, url in pages:
                if self.stop_requested:
                    break

                self.log(f"Проверка страницы: {title}")
                external_links = self.fetch_external_links(url)

                if not external_links:
                    self.log("Внешние ссылки не найдены")
                    continue

                self.log(f"Найдено {len(external_links)} внешних ссылок")

                for link in external_links:
                    if self.stop_requested:
                        break

                    domain = self.get_domain(link)
                    if not domain:
                        continue

                    self.log(f"Проверяем домен: {domain}")

                    # Дата проверки
                    check_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Проверяем доступность домена
                    is_available = self.check_domain_availability(domain)
                    self.log(f"  Доступность: {'доступен' if is_available else 'занят'}")

                    # Проверяем Archive.org
                    archive_info = self.check_archive_org(domain)
                    archive_text = archive_info if archive_info else "не найден"

                    # Получаем количество снимков
                    snapshots_count = 0
                    if self.check_snapshots_var.get():
                        snapshots_count = self.get_archive_snapshots_count(domain)

                    # Извлекаем содержимое страницы
                    page_title = "Не извлекалось"
                    page_preview = "Не извлекалось"

                    if self.extract_content_var.get():
                        page_title, page_preview = self.extract_page_content(link)

                    # Сохраняем результат
                    self.all_checked_domains.append((
                        keyword,
                        title,
                        link,
                        domain,
                        "Доступен" if is_available else "Занят",
                        archive_text,
                        snapshots_count,
                        check_date,
                        page_title,
                        page_preview
                    ))

                    if is_available:
                        self.log(f"  ✓ Домен {domain} доступен")
                        self.results.append((keyword, title, link, domain, archive_text))
                    else:
                        self.log(f"  ✗ Домен {domain} занят")

                    # Пауза между запросами
                    time.sleep(random.uniform(1.0, 2.0))

        except Exception as e:
            self.log(f"Ошибка: {e}")

        self.finish_check()

    def finish_check(self):
        self.is_running = False
        self.progress.stop()
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

        if self.results:
            self.log(f"\nНайдено {len(self.results)} доступных доменов")
            self.log(f"Всего проверено доменов: {len(self.all_checked_domains)}")
            self.status_label.config(text="Готово", fg="green")
        else:
            if self.all_checked_domains:
                self.log(f"\nДоступные домены не найдены")
                self.log(f"Всего проверено доменов: {len(self.all_checked_domains)}")
                self.status_label.config(text="Готово", fg="green")
            else:
                self.log("\nДомены для проверки не найдены")
                self.status_label.config(text="Готово", fg="green")

    def search_wikipedia(self, keywords, language):
        user_agent = "WikiLinkChecker/1.0"
        wiki_wiki = wikipediaapi.Wikipedia(
            language=language,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent=user_agent
        )

        results = []
        for keyword in keywords:
            if self.stop_requested:
                break

            try:
                page = wiki_wiki.page(keyword)
                if page.exists():
                    results.append((keyword, page.title, page.fullurl))
                    continue

                search_results = wiki_wiki.search(keyword, results=5)
                for search_result in search_results:
                    if self.stop_requested:
                        break
                    page = wiki_wiki.page(search_result)
                    if page.exists():
                        results.append((keyword, page.title, page.fullurl))

            except Exception as e:
                self.log(f"Ошибка при поиске '{keyword}': {e}")
                continue

        return results

    def fetch_external_links(self, page_url):
        try:
            headers = {"User-Agent": "WikiLinkChecker/1.0"}
            response = requests.get(page_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return set()

            soup = BeautifulSoup(response.text, 'html.parser')
            external_links = set()

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith(('http://', 'https://')):
                    if 'wikipedia.org' not in href and 'wikimedia.org' not in href:
                        external_links.add(href)

            return external_links
        except Exception as e:
            self.log(f"Ошибка при извлечении ссылок: {e}")
            return set()

    def get_domain(self, url):
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]

            # Фильтруем нежелательные домены
            if not domain or ':' in domain or 'archive.org' in domain or 'wayback' in domain:
                return None

            return domain
        except:
            return None

    def check_archive_org(self, domain):
        try:
            self.log(f"    Проверяем Archive.org для {domain}")
            # Используем CDX API для проверки наличия снимков
            url = f"https://web.archive.org/cdx/search/cdx?url={domain}&limit=1"
            headers = {"User-Agent": "WikiLinkChecker/1.0"}

            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code != 200:
                self.log(f"    Archive.org недоступен (код {response.status_code})")
                return "Archive.org недоступен"

            text = response.text.strip()
            if not text:
                self.log(f"    ✗ Снимки не найдены")
                return "снимки не найдены"

            # Парсим первую строку CDX для получения даты
            lines = text.split('\n')
            if lines and lines[0].strip():
                parts = lines[0].split(' ')
                if len(parts) >= 2:
                    timestamp = parts[1]
                    if len(timestamp) >= 8:
                        date_str = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
                        self.log(f"    ✓ Найден снимок: {date_str}")
                        return f"последний снимок {date_str}"

            self.log(f"    ✓ Найдены снимки")
            return "найдены снимки"

        except Exception as e:
            self.log(f"    ⚠ Ошибка Archive.org для {domain}: {e}")
            return "ошибка Archive.org"

    def check_domain_availability(self, domain):
        try:
            if whois:
                try:
                    w = whois.whois(domain)
                    if w.domain_name:
                        return False
                except:
                    pass

            try:
                answers = dns.resolver.resolve(domain, 'A')
                return False
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return True
            except:
                return False

        except Exception as e:
            self.log(f"Ошибка проверки домена {domain}: {e}")
            return False

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = WikiDomainChecker()
    app.run()
