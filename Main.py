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
            }
            needed_cols = list(rename_dict.keys()) + ["DODID"]

            Roster_new = Roster_new[needed_cols].rename(columns=rename_dict)
            Roster_old = Roster_old[needed_cols].rename(columns=rename_dict)

            Roster_new = Roster_new.merge(Decode, on="UIC", how="left")
            Roster_old = Roster_old.merge(Decode, on="UIC", how="left")

            for col in ["BDE", "BN", "CTB"]:
                if col not in Roster_new.columns:
                    Roster_new[col] = ""
                if col not in Roster_old.columns:
                    Roster_old[col] = ""

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
                    IL5_Child_Group2=df.get("BDE", ""),
                    IL5_Child_Group3=df.get("BN", ""),
                    IL5_Child_Group4=df.get("CTB", ""),
                    IL5_Child_Role=""
                )[["FirstName", "LastName", "Username", "Email Address", "DateofBirth", "Known_As",
                    "UUID", "IL5_OHWS_Group1", "IL5_OHWS_Group2", "IL5_OHWS_Role", "IL5_Child_Group1",
                    "IL5_Child_Group2", "IL5_Child_Group3", "IL5_Child_Group4", "IL5_Child_Role"]]

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

            # Create in-memory ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                zip_file.writestr("gains.csv", gains.to_csv(index=False))
                zip_file.writestr("losses.csv", losses.to_csv(index=False))
                zip_file.writestr("alpha.csv", Alpha.to_csv(index=False))
                zip_file.writestr("missing_uics.csv", UICs.to_csv(index=False))
            zip_buffer.seek(0)

            st.download_button(
                "Download All Reports as ZIP", data=zip_buffer, file_name="roster_reports.zip", mime="application/zip"
            )

if __name__ == "__main__":
    main()
