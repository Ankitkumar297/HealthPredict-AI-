# Assessment walkthrough

1. Start backend and frontend, then open the dashboard.
2. Select **Assessment tests** and run the supplied ten rows once on a fresh database. The original dotted dates remain visible. The runner converts valid notation to slashes for normal validation.
3. John Hunter is rejected for an invalid email; Peter Larry for an impossible date; Kris Wu for both a future date and invalid email. Seven rows are accepted, including both identical Robyn Pears rows with different IDs. No AI call is attempted automatically.
4. Open **Patients** and show all seven records. Select one, edit its email to `gokul@infocare.com`, and show its detail page.
5. Delete one saved record using the confirmation dialog, then show the final six records.
6. If a real provider key is configured, open a patient and run AI assessment. If no key is present, show the explicit configuration failure and failed status with no remarks.

Run on a clean database for the exact counts. Existing local records add to the list.
