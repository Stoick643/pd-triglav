# 🏔️ PD Triglav — Navodila za beta testiranje

## Prijava

Pojdi na **https://pd-triglav.fly.dev/auth/login** in se prijavi z enim od testnih računov:

| Vloga | Email | Geslo |
|-------|-------|-------|
| 👤 **Član** | clan@pd-triglav.si | *(sporočeno posebej)* |
| 🏔️ **Vodnik** | vodnik@pd-triglav.si | *(sporočeno posebej)* |

---

## 👤 Testiranje kot ČLAN

### 1. Domača stran
- [ ] Oglej si domačo stran — hero slika, zgodovinski dogodek dneva, novice
- [ ] Klikni na zgodovinski dogodek za podrobnosti
- [ ] Preveri ali se novice pravilno prikazujejo

### 2. Izleti
- [ ] Pojdi na **Izleti → Objave izletov** — preglej seznam
- [ ] Klikni na izlet za podrobnosti
- [ ] **Prijavi se** na izlet (gumb "Prijava")
- [ ] Preveri da si na seznamu udeležencev
- [ ] **Odjavi se** z izleta
- [ ] Pojdi na **Izleti → Koledar izletov** — preglej koledar
- [ ] Pojdi na **Izleti → Moji izleti** — preglej svoje prijave

### 3. Poročila
- [ ] Pojdi na **Poročila → Vsa poročila**
- [ ] Oglej si poročilo (če obstaja)

### 4. Splošno
- [ ] Pojdi na **O klubu**
- [ ] Preveri navigacijo na telefonu (stranski meni)
- [ ] Preveri ali stran deluje na telefonu (responsive)

---

## 🏔️ Testiranje kot VODNIK (Trip Leader)

*Najprej naredi vse iz članske sekcije zgoraj, nato še:*

### 5. Ustvarjanje izleta
- [ ] Pojdi na **Izleti → Nova objava**
- [ ] Izpolni obrazec:
  - Naslov (npr. "Testni izlet na Šmarno goro")
  - Opis
  - Cilj
  - Datum, ura zbiranja, zbirno mesto
  - Težavnost
  - Maks. udeležencev
  - Potrebna oprema
  - Cena
- [ ] Shrani in preveri da se izlet prikaže na seznamu

### 6. Urejanje izleta
- [ ] Odpri svoj izlet in klikni **Uredi**
- [ ] Spremeni kakšen podatek in shrani
- [ ] Preveri da so spremembe vidne

### 7. Upravljanje izleta
- [ ] Preveri seznam prijavljenih udeležencev
- [ ] Poskusi **preklicati** izlet

---

## ⚙️ Testiranje kot ADMIN (Skrbnik)

*Najprej naredi vse iz članske in vodniške sekcije zgoraj, nato še:*

### 8. Administracija — upravljanje uporabnikov
- [ ] Pojdi na **Administracija** (v stranskem meniju)
- [ ] Preglej seznam čakajočih uporabnikov
- [ ] **Odobri** testnega čakajočega uporabnika (pending@pd-triglav.si)
- [ ] Preveri da se vloga spremeni
- [ ] Ustvari novega uporabnika z registracijo (drug email) in ga nato **zavrni**

### 9. Administracija — vsebina
- [ ] Na domači strani klikni **Regeneriraj** za zgodovinski dogodek dneva
- [ ] Preveri da se nov dogodek prikaže
- [ ] Klikni **Osveži novice** za posodobitev novic
- [ ] Preveri da se novice posodobijo

### 10. Nadzorna plošča
- [ ] Pojdi na **Nadzorna plošča**
- [ ] Preglej pregled uporabnikov, izletov, statistike

### 11. Admin + Vodnik kombinacija
- [ ] Ustvari izlet kot admin
- [ ] Preveri da se prikaže na seznamu in v koledarju

---

| Vloga | Email | Geslo |
|-------|-------|-------|
| ⚙️ **Admin** | admin@pd-triglav.si | *(sporočeno posebej)* |

---

## 📝 Povratne informacije

Ko najdeš napako ali imaš predlog, zapiši:
1. **Kaj** si naredil (koraki)
2. **Kaj** se je zgodilo (napaka / nepričakovano obnašanje)
3. **Kaj** si pričakoval
4. **Kje** (telefon / računalnik, kateri brskalnik)

Pošlji na: *(kontakt oseba)*

---

**Hvala za pomoč pri testiranju! 🙏🏔️**
