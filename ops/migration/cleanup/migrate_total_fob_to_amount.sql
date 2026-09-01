-- One-time migration: total_fob was incorrectly named (it holds TotalAmount from legacy)
-- Copy to total_amount before dropping the column via module upgrade
UPDATE sis_document
SET total_amount = total_fob
WHERE total_fob IS NOT NULL AND total_fob != 0
  AND (total_amount IS NULL OR total_amount = 0);
