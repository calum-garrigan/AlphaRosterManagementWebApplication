import pandas as pd
import streamlit as st
import zipfile
import io

def main():
    st.set_page_config(page_title="Roster Updater", layout="wide")

    st.image("Jag Logo.png", width=200)
    st.title("Alpha Roster Management Web Application")
    st.write("Upload your rosters and decoder, then generate Gains, Losses, and Alpha rosters.")

    new_roster_file = st.file_uploader("Upload New Roster CSV", type="csv")
    old_roster_file = st.file_uploader("Upload Old Roster CSV", type="csv")
    decoder_file = st.file_uploader("Upload Decoder CSV", type="csv")

    if st.button("Generate Gains/Losses/Alpha"):
        if not (new_roster_file and old_roster_file and decoder_file):
            st.warning("Please upload all three CSV files before proceeding.")
        else:
            Roster_new = pd.read_csv(new_roster_file, dtype={"DODID": str})
            Roster_old = pd.read_csv(old_roster_file, dtype={"DODID": str})
            Decode = pd.read_csv(decoder_file)

            Roster_new = Roster_new.drop_duplicates(subset="DODID")
            Roster_old = Roster_old.drop_duplicates(subset="DODID")

            rename_dict = {
                "First Name": "FirstName",
                "Last Name": "LastName",
                "Birthdate": "DateofBirth",
                "Email Address": "Email Address",
                "Current Rank": "Rank",
                "Soldier Home UIC": "UIC",
                "Known As": "Known As"
            }
            needed_cols = list(rename_dict.keys()) + ["DODID"]

            Roster_new = (
                Roster_new[needed_cols]
                .rename(columns=rename_dict)
            )
            Roster_old = (
                Roster_old[needed_cols]
                .rename(columns=rename_dict)
            )

            Roster_new["UIC"] = Roster_new["UIC"].astype(str).str.strip()
            Roster_old["UIC"] = Roster_old["UIC"].astype(str).str.strip()
            Decode["UIC"] = Decode["UIC"].astype(str).str.strip()

            Roster_new = Roster_new.merge(Decode, on="UIC", how="left")
            Roster_old = Roster_old.merge(Decode, on="UIC", how="left")

            UICs = Roster_new[Roster_new['Group'].isna()]

            merge_cols = ["DODID", "FirstName", "LastName"]
            gains_mask = ~Roster_new[merge_cols].apply(tuple, axis=1).isin(
                Roster_old[merge_cols].apply(tuple, axis=1)
            )
            losses_mask = ~Roster_old[merge_cols].apply(tuple, axis=1).isin(
                Roster_new[merge_cols].apply(tuple, axis=1)
            )
            gains = Roster_new.loc[gains_mask].copy()
            losses = Roster_old.loc[losses_mask].copy()

            # --- Adjust Gains & Losses Format ---
            def format_roster(df):
                df["Username"] = df["DODID"]
                df["UUID"] = df["DODID"]
                df["IL5 Child Group1"] = "All Users"
                df.rename(columns={"BDE": "IL5 Child Group2", "BN": "IL5 Child Group3", "CTB": "IL5 Child Group4"}, inplace=True)
                
                # Set correct order of columns
                column_order = [
                    "FirstName", "LastName", "Username", "Email Address", "DateofBirth", "Known As",
                    "UUID", "IL5 OHWS Group1", "IL5 OHWS Group2", "IL5 OHWS Role",
                    "IL5 Child Group1", "IL5 Child Group2", "IL5 Child Group3", "IL5 Child Group4", "IL5 Child Role"
                ]
                
                return df[column_order]

            gains = format_roster(gains)
            losses = format_roster(losses)

            # --- Alpha Roster ---
            Alpha = pd.DataFrame({
                "About": Roster_new["LastName"] + " " + Roster_new["FirstName"],
                "DODID": Roster_new["DODID"],
                "UIC": Roster_new["UIC"]
            })

            st.subheader("Gains")
            st.dataframe(gains)

            st.subheader("Losses")
            st.dataframe(losses)

            st.subheader("Alpha Roster")
            st.dataframe(Alpha)

            # --- Creating a ZIP file for download ---
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                zipf.writestr("gains.csv", gains.to_csv(index=False))
                zipf.writestr("losses.csv", losses.to_csv(index=False))
                zipf.writestr("alpha.csv", Alpha.to_csv(index=False))
                zipf.writestr("UICs.csv", UICs.to_csv(index=False))

            zip_buffer.seek(0)
            st.download_button(
                label="Download All CSVs",
                data=zip_buffer,
                file_name="roster_outputs.zip",
                mime="application/zip"
            )

            # Display a pop-up message for Missing UICs
            st.warning("Please double-check the Missing UICs CSV!")

if __name__ == "__main__":
    main()
