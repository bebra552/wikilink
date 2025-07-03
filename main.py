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

try:
    import whois
except ImportError:
    whois = None

class WikiDomainChecker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WikiLink Domain Checker")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.results = []
        self.is_running = False
        self.stop_requested = False
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        title_label = tk.Label(self.root, text="WikiLink Domain Checker", 
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
        tk.Label(self.root, text="Лог:").pack(pady=(10,0))
        self.log_text = scrolledtext.ScrolledText(self.root, height=12, width=70)
        self.log_text.pack(pady=5, padx=20, fill='both', expand=True)
        
        # Кнопки сохранения
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.save_csv_button = tk.Button(button_frame, text="Сохранить CSV", 
                                        command=self.save_csv, state='disabled')
        self.save_csv_button.pack(side='left', padx=5)
        
        self.save_excel_button = tk.Button(button_frame, text="Сохранить Excel", 
                                          command=self.save_excel, state='disabled')
        self.save_excel_button.pack(side='left', padx=5)
        
        # Кнопка связи
        contact_button = tk.Button(button_frame, text="Связь", 
                                  command=self.open_contact, bg="#2196F3", fg="white")
        contact_button.pack(side='left', padx=5)
        
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
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
        self.save_csv_button.config(state='disabled')
        self.save_excel_button.config(state='disabled')
        self.progress.start()
        self.status_label.config(text="Проверка...", fg="orange")
        self.log_text.delete(1.0, tk.END)
        self.results = []
        
        thread = threading.Thread(target=self.check_domains, args=(keywords, language))
        thread.start()
        
    def stop_check(self):
        self.stop_requested = True
        self.log("Остановка проверки...")
        
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
                    
                self.log(f"Проверка страницы: {title} ({url})")
                external_links = self.fetch_external_links(url)
                
                if not external_links:
                    self.log("Внешние ссылки не найдены")
                    continue
                    
                self.log(f"Найдено {len(external_links)} внешних ссылок. Проверяем доступность доменов...")
                
                for link in external_links:
                    if self.stop_requested:
                        break
                        
                    domain = self.get_domain(link)
                    if not domain or ':' in domain:
                        continue
                        
                    self.log(f"Проверяем домен: {domain}")
                    
                    if self.check_domain_availability(domain):
                        self.log(f"  ✓ Домен {domain} доступен")
                        self.results.append((keyword, title, link, domain))
                    else:
                        self.log(f"  ✗ Домен {domain} занят")
                    
                    time.sleep(random.uniform(0.5, 1.0))
                    
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
            self.save_csv_button.config(state='normal')
            self.save_excel_button.config(state='normal')
            self.status_label.config(text="Готово", fg="green")
        else:
            self.log("\nДоступные домены не найдены")
            self.status_label.config(text="Готово", fg="green")
            
    def search_wikipedia(self, keywords, language):
        user_agent = "WikiLinkChecker/1.0"
        wiki_wiki = wikipediaapi.Wikipedia(
            language=language,  # Используем переданный язык
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent=user_agent
        )
        
        results = []
        for keyword in keywords:
            if self.stop_requested:
                break
                
            try:
                # Сначала пытаемся найти точное совпадение
                page = wiki_wiki.page(keyword)
                if page.exists():
                    results.append((keyword, page.title, page.fullurl))
                    continue
                
                # Если точное совпадение не найдено, используем поиск
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
                    # Фильтруем ссылки на саму Wikipedia
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
            # Убираем www. если есть
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return None
            
    def check_domain_availability(self, domain):
        try:
            # Проверяем через whois если доступен
            if whois:
                try:
                    w = whois.whois(domain)
                    if w.domain_name:
                        return False
                except:
                    pass
                    
            # Проверяем через DNS
            try:
                answers = dns.resolver.resolve(domain, 'A')
                return False  # Если есть A-записи, домен занят
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return True  # Домен доступен
            except:
                return False  # Ошибка - считаем домен недоступным
                
        except Exception as e:
            self.log(f"Ошибка проверки домена {domain}: {e}")
            return False
            
    def save_csv(self):
        if not self.results:
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Ключевое слово", "Статья", "Ссылка", "Домен"])
                    writer.writerows(self.results)
                messagebox.showinfo("Успех", f"Сохранено: {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
                
    def save_excel(self):
        if not self.results:
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if filepath:
            try:
                df = pd.DataFrame(self.results, 
                                columns=["Ключевое слово", "Статья", "Ссылка", "Домен"])
                df.to_excel(filepath, index=False)
                messagebox.showinfo("Успех", f"Сохранено: {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
                
    def open_contact(self):
        webbrowser.open("https://t.me/Userspoi")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = WikiDomainChecker()
    app.run()
