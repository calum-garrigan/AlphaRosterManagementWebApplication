import pandas as pd
import streamlit as st

def main():
    st.set_page_config(page_title="Roster Updater", layout="wide")
    st.image("Jag Logo.png", width=200)
    st.title("Alpha Roster Management Web Application")
    st.write("Upload your rosters and decoder, then generate Gains, Losses, and Alpha rosters.")

    new_roster_file = st.file_uploader("Upload New Roster CSV", type="csv")
    old_roster_file = st.file_uploader("Upload Old Roster CSV", type="csv")
    decoder_file    = st.file_uploader("Upload Decoder CSV", type="csv")

    if st.button("Generate Gains/Losses/Alpha"):
        if not (new_roster_file and old_roster_file and decoder_file):
            st.warning("Please upload all three CSV files before proceeding.")
        else:
            Roster_new = pd.read_csv(new_roster_file, dtype={"DODID": str})
            Roster_old = pd.read_csv(old_roster_file, dtype={"DODID": str})
            Decode     = pd.read_csv(decoder_file)

            Roster_new = Roster_new.drop_duplicates(subset="DODID")
            Roster_old = Roster_old.drop_duplicates(subset="DODID")

            rename_dict = {
                "First Name": "FirstName",
                "Last Name": "LastName",
                "Birthdate": "DateofBirth",
                "Email Address": "Email Address",
                "Current Rank": "Rank",
                "Soldier Home UIC": "UIC",
            }

            needed_cols = list(rename_dict.keys()) + ["DODID"]

            Roster_new = Roster_new[needed_cols].rename(columns=rename_dict)
            Roster_old = Roster_old[needed_cols].rename(columns=rename_dict)

            Roster_new["UIC"] = Roster_new["UIC"].astype(str).str.strip()
            Roster_old["UIC"] = Roster_old["UIC"].astype(str).str.strip()
            Decode["UIC"] = Decode["UIC"].astype(str).str.strip()

            Roster_new = Roster_new.merge(Decode, on="UIC", how="left")
            Roster_old = Roster_old.merge(Decode, on="UIC", how="left")

            gains_mask  = ~Roster_new["DODID"].isin(Roster_old["DODID"])
            losses_mask = ~Roster_old["DODID"].isin(Roster_new["DODID"])
            gains  = Roster_new.loc[gains_mask].copy()
            losses = Roster_old.loc[losses_mask].copy()

            for df in [gains, losses]:
                df["Username"] = df["DODID"]
                df["UUID"] = df["DODID"]
                df["Known As"] = ""
                df["IL5 OHWS Group1"] = ""
                df["IL5 OHWS Group2"] = ""
                df["IL5 OHWS Role"] = ""
                df["IL5 Child Group1"] = "All Users"
                df["IL5 Child Group2"] = df["BDE"]
                df["IL5 Child Group3"] = df["BN"]
                df["IL5 Child Group4"] = df["CTB"]
                df["IL5 Child Role"] = ""
                df.drop(columns=["Raw name", "Detachment"], errors='ignore', inplace=True)

            Alpha = pd.DataFrame({
                "About": Roster_new["LastName"] + " " + Roster_new["FirstName"],
                "DODID": Roster_new["DODID"],
                "Rank":  Roster_new["Rank"],
                "UIC":   Roster_new["UIC"]
            })
            
            st.subheader("Gains")
            st.dataframe(gains)
            
            st.subheader("Losses")
            st.dataframe(losses)
            
            st.subheader("Alpha Roster")
            st.dataframe(Alpha)
            
            st.download_button(
                label="Download Gains as CSV",
                data=gains.to_csv(index=False, quoting=3),
                file_name="gains.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Losses as CSV",
                data=losses.to_csv(index=False, quoting=3),
                file_name="losses.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Alpha as CSV",
                data=Alpha.to_csv(index=False, quoting=3),
                file_name="alpha.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
