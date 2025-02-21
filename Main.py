import pandas as pd
import streamlit as st

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
            }
            needed_cols = list(rename_dict.keys()) + ["DODID"]

            Roster_new = Roster_new[needed_cols].rename(columns=rename_dict)
            Roster_old = Roster_old[needed_cols].rename(columns=rename_dict)

            Roster_new = Roster_new.merge(Decode, on="UIC", how="left")
            Roster_old = Roster_old.merge(Decode, on="UIC", how="left")

            merge_cols = ["DODID", "FirstName", "LastName"]
            gains_mask = ~Roster_new[merge_cols].apply(tuple, axis=1).isin(Roster_old[merge_cols].apply(tuple, axis=1))
            losses_mask = ~Roster_old[merge_cols].apply(tuple, axis=1).isin(Roster_new[merge_cols].apply(tuple, axis=1))

            gains = Roster_new.loc[gains_mask].copy()
            losses = Roster_old.loc[losses_mask].copy()

            def format_output(df):
                return df.assign(
                    Username=df["DODID"],
                    UUID=df["DODID"],
                    Known_As="",
                    IL5_OHWS_Group1="",
                    IL5_OHWS_Group2="",
                    IL5_OHWS_Role="",
                    IL5_Child_Group1="All Users",
                    IL5_Child_Group2=df["BDE"],
                    IL5_Child_Group3=df["BN"],
                    IL5_Child_Group4=df["CTB"],
                    IL5_Child_Role=""
                )[[
                    "FirstName", "LastName", "Username", "Email Address", "DateofBirth", "Known_As",
                    "UUID", "IL5_OHWS_Group1", "IL5_OHWS_Group2", "IL5_OHWS_Role", "IL5_Child_Group1",
                    "IL5_Child_Group2", "IL5_Child_Group3", "IL5_Child_Group4", "IL5_Child_Role"
                ]]

            gains = format_output(gains)
            losses = format_output(losses)

            st.subheader("Gains")
            st.dataframe(gains)
            st.subheader("Losses")
            st.dataframe(losses)

            st.download_button("Download Gains as CSV", data=gains.to_csv(index=False), file_name="gains.csv", mime="text/csv")
            st.download_button("Download Losses as CSV", data=losses.to_csv(index=False), file_name="losses.csv", mime="text/csv")

if __name__ == "__main__":
    main()
