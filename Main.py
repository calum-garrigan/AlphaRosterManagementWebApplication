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

            UICs = Roster_new[Roster_new['BDE'].isna()]
            
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

            Alpha = pd.DataFrame({
                "About": Roster_new["LastName"] + " " + Roster_new["FirstName"],
                "DODID": Roster_new["DODID"],
                "Rank": Roster_new["Rank"],
                "UIC": Roster_new["UIC"]
            })

            if "CTB" in Roster_new.columns:
                Alpha["CTB"] = Roster_new["CTB"]
            if "BN" in Roster_new.columns:
                Alpha["BN"] = Roster_new["BN"]

            st.subheader("Gains")
            st.dataframe(gains)
            st.subheader("Losses")
            st.dataframe(losses)
            st.subheader("Alpha Roster")
            st.dataframe(Alpha)

            st.download_button("Download Gains as CSV", data=gains.to_csv(index=False), file_name="gains.csv", mime="text/csv")
            st.download_button("Download Losses as CSV", data=losses.to_csv(index=False), file_name="losses.csv", mime="text/csv")
            st.download_button("Download Alpha as CSV", data=Alpha.to_csv(index=False), file_name="alpha.csv", mime="text/csv")
            st.download_button("Download Missing UICs as CSV", data=UICs.to_csv(index=False), file_name="missing_uics.csv", mime="text/csv")

if __name__ == "__main__":
    main()
