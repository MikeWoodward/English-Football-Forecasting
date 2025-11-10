# CSV to Database Column Mapping Report

## Summary
All CSV columns are correctly mapped to database columns with the same names. 
No discrepancies found.

---

## 1. League Table

### CSV Columns (`league.csv`):
```
league_id, season, league_tier, league_name, season_start, season_end, 
league_size_matches, league_size_clubs, league_notes
```

### Database Table Columns:
```
league_id, season, league_tier, league_name, season_start, season_end,
league_size_matches, league_size_clubs, league_notes
```

### Code Mapping:
- CSV column → Database column: All match ✓
- INSERT statement: `league_id, season, league_tier, league_name, season_start, season_end, league_size_matches, league_size_clubs, league_notes`

**Status: ✓ All columns match**

---

## 2. Football Match Table

### CSV Columns (`football_match.csv`):
```
league_id, match_id, match_date, attendance
```

### Database Table Columns:
```
match_id, league_id, match_date, attendance
```

### Code Mapping:
- CSV column → Database column: All match ✓
- INSERT statement: `match_id, league_id, match_date, attendance`
- Note: Column order differs between CSV and DB table, but all columns are correctly mapped

**Status: ✓ All columns match**

---

## 3. Club History Table

### CSV Columns (`club_history.csv`):
```
club_name_year_changed_id, club_name, nickname, modern_name, year_changed,
date_changed, notes, wikipedia
```

### Database Table Columns:
```
club_name_year_changed_id, club_name, nickname, modern_name, year_changed,
date_changed, notes, wikipedia
```

### Code Mapping:
- CSV column → Database column: All match ✓
- INSERT statement: `club_name_year_changed_id, club_name, nickname, modern_name, year_changed, date_changed, notes, wikipedia`

**Status: ✓ All columns match**

---

## 4. Club Season Table

### CSV Columns (`club_season.csv`):
```
league_id, club_name, squad_size, foreigner_count, foreigner_fraction,
mean_age, total_market_value, club_league_id
```

### Database Table Columns:
```
league_id, club_name, club_league_id, squad_size, foreigner_count,
foreigner_fraction, mean_age, total_market_value
```

### Code Mapping:
- CSV column → Database column: All match ✓
- INSERT statement: `league_id, club_name, squad_size, foreigner_count, foreigner_fraction, mean_age, total_market_value, club_league_id`
- Note: Column order differs between CSV and DB table, but `club_league_id` is correctly placed at the end in the INSERT statement

**Status: ✓ All columns match**

---

## 5. Club Match Table

### CSV Columns (`club_match.csv`):
```
match_id, club_name, goals, red_cards, yellow_cards, fouls, is_home, 
club_match_id
```

### Database Table Columns:
```
match_id, club_match_id, club_name, goals, red_cards, yellow_cards, fouls,
is_home
```

### Code Mapping:
- **❌ DISCREPANCY FOUND**

**Tuple order in code (lines 483-496):**
1. match_id
2. club_name
3. goals
4. red_cards
5. yellow_cards
6. fouls
7. is_home
8. club_match_id

**INSERT statement order (lines 502-506):**
1. match_id
2. club_match_id
3. club_name
4. goals
5. red_cards
6. yellow_cards
7. fouls
8. is_home

**Issue:** The tuple values are in the CSV order, but the INSERT statement expects `club_match_id` in position 2. This means:
- `match_id` → `match_id` ✓
- `club_name` (tuple pos 2) → `club_match_id` (DB pos 2) ✗ **WRONG**
- `goals` (tuple pos 3) → `club_name` (DB pos 3) ✗ **WRONG**
- All subsequent columns are shifted incorrectly

**Status: ❌ MISMATCH - Tuple order does not match INSERT statement order**

---

## 6. Attendance Violin Table

### CSV Columns (`attendance_violin.csv`):
```
attendance, probability_density, league_id, attendance_league_id
```

### Database Table Columns:
```
attendance, probability_density, league_id, attendance_league_id
```

### Code Mapping:
- CSV column → Database column: All match ✓
- INSERT statement: `attendance, probability_density, league_id, attendance_league_id`

**Status: ✓ All columns match**

---

## Conclusion

**❌ DISCREPANCY FOUND in Club Match Table**

### Summary:
- **5 tables:** All CSV columns correctly mapped to database columns ✓
- **1 table (club_match):** Tuple order mismatch with INSERT statement ❌

### Discrepancy Details:
The `club_match` table has a critical mapping error:
- The tuple values follow the CSV column order
- The INSERT statement expects `club_match_id` in position 2, but the tuple has it in position 8
- This causes all columns after `match_id` to be inserted into the wrong database columns

### Recommendation:
Fix the tuple order in `load_database_table_club_match()` to match the INSERT statement order:
```python
club_match_records = [
    (
        row['match_id'],
        str(row['club_match_id']),  # Move to position 2
        row['club_name'],
        int(row['goals']) if pd.notna(row['goals']) else 0,
        int(row['red_cards']) if pd.notna(row['red_cards']) else None,
        int(row['yellow_cards']) if pd.notna(row['yellow_cards']) else None,
        int(row['fouls']) if pd.notna(row['fouls']) else None,
        bool(row['is_home']) if pd.notna(row['is_home']) else False
    )
    for _, row in club_match_data.iterrows()
]
```

