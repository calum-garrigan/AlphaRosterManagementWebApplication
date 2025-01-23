import pandas as pd
import streamlit as st

def main():
    st.set_page_config(page_title="Roster Updater", layout="wide")
    st.image("Jag Logo.png", width=200)

    st.title("Alpha Roster Management Web Application")
    st.write("Upload your rosters and decoder, then generate Gains, Losses, and Alpha rosters.")

    # -- File uploader widgets --
    new_roster_file = st.file_uploader("Upload New Roster CSV", type="csv")
    old_roster_file = st.file_uploader("Upload Old Roster CSV", type="csv")
    decoder_file    = st.file_uploader("Upload Decoder CSV",     type="csv")

    if st.button("Generate Gains/Losses/Alpha"):
        if not (new_roster_file and old_roster_file and decoder_file):
            st.warning("Please upload all three CSV files before proceeding.")
        else:
            # --- Read CSV data ---
            Roster_new = pd.read_csv(new_roster_file)
            Roster_old = pd.read_csv(old_roster_file)
            Decode     = pd.read_csv(decoder_file)

            # ---------------------------------------------------------
            # A) Rename only the columns that changed in your new CSVs
            #
            #    The keys below should match the **exact** column names
            #    in your new rosters. The values are what we'll call
            #    them *inside* the code for consistency.
            # ---------------------------------------------------------
            rename_dict = {
                "First Name":  "First",
                "Last Name":   "Last",
                "Birthdate":   "DOB",
                "Email Address": "Email",

                "Home UIC":    "UIC",   # replaces old "Soldier Home UIC"
                "Rank":        "Rank",  # replaces old "Current Rank"

                "Employee ID (EMPLID)": "EMPLID",  # brand new column
                "Battalion":   "BN",    # was "BN" in older code
                "DMSL (Distribution Management Sub-Level - Current Only)": "CTB"  # was "CTB"
            }

            # We still have a separate "DODID" column that remains the same
            # since you said "No DODID is separate, keep it as is."

            # -- Drop duplicates based on DODID (still your unique ID) --
            Roster_new = Roster_new.drop_duplicates(subset="DODID")
            Roster_old = Roster_old.drop_duplicates(subset="DODID")

            # -- Select columns that exist and rename them --
            #    Make sure the columns in 'rename_dict' actually appear in your CSVs.
            existing_cols_in_new = [col for col in rename_dict if col in Roster_new.columns]
            existing_cols_in_old = [col for col in rename_dict if col in Roster_old.columns]

            Roster_new = Roster_new[existing_cols_in_new + ["DODID"]].rename(columns=rename_dict)
            Roster_old = Roster_old[existing_cols_in_old + ["DODID"]].rename(columns=rename_dict)

            # -- Optionally title-case first/last names --
            if "First" in Roster_new.columns:
                Roster_new["First"] = Roster_new["First"].str.title()
                Roster_old["First"] = Roster_old["First"].str.title()
            if "Last" in Roster_new.columns:
                Roster_new["Last"] = Roster_new["Last"].str.title()
                Roster_old["Last"] = Roster_old["Last"].str.title()

            # ---------------------------------------------------------
            # B) Merge the Decode file on "UIC" if it exists
            # ---------------------------------------------------------
            if "Raw" in Decode.columns:
                Decode.drop(columns="Raw", inplace=True)

            # If your Decode file also uses "Home UIC" in the new format,
            # be sure to rename that to "UIC" in Decode as well before merging.
            if "Home UIC" in Decode.columns:
                Decode.rename(columns={"Home UIC": "UIC"}, inplace=True)

            Roster_new = Roster_new.merge(Decode, on="UIC", how="left")
            Roster_old = Roster_old.merge(Decode, on="UIC", how="left")

            # ---------------------------------------------------------
            # C) Gains & Losses
            # ---------------------------------------------------------
            # We match on DODID plus optional First/Last if present.
            merge_cols = ["DODID"]
            if all(col in Roster_new.columns for col in ["First", "Last"]):
                merge_cols = ["DODID", "First", "Last"]

            gains_mask  = ~Roster_new[merge_cols].apply(tuple, axis=1).isin(
                            Roster_old[merge_cols].apply(tuple, axis=1)
                          )
            losses_mask = ~Roster_old[merge_cols].apply(tuple, axis=1).isin(
                            Roster_new[merge_cols].apply(tuple, axis=1)
                          )
            gains  = Roster_new.loc[gains_mask].copy()
            losses = Roster_old.loc[losses_mask].copy()

            # ---------------------------------------------------------
            # D) Alpha Roster
            # ---------------------------------------------------------
            # The code used to look for CTB/BN. Now we have them renamed
            # from "DMSL (Distribution Management Sub-Level - Current Only)"
            # and "Battalion". After rename_dict, they are "CTB" and "BN".
            columns_for_alpha = []
            if "CTB" in Roster_new.columns:
                columns_for_alpha.append("CTB")
            if "BN" in Roster_new.columns:
                columns_for_alpha.append("BN")

            # Build the Alpha dataframe
            # Keep "DODID" as is, but also include "Rank", "EMPLID", etc. if desired.
            Alpha = pd.DataFrame({"DODID": Roster_new["DODID"]})
            if "Rank" in Roster_new.columns:
                Alpha["Rank"] = Roster_new["Rank"]
            if "EMPLID" in Roster_new.columns:
                Alpha["EMPLID"] = Roster_new["EMPLID"]
            if all(col in Roster_new.columns for col in ["First", "Last"]):
                Alpha["About"] = Roster_new["Last"] + " " + Roster_new["First"]

            for col in columns_for_alpha:
                Alpha[col] = Roster_new[col]

            # ---------------------------------------------------------
            # E) Display and download results
            # ---------------------------------------------------------
            st.subheader("Gains")
            st.dataframe(gains)

            st.subheader("Losses")
            st.dataframe(losses)

            st.subheader("Alpha Roster")
            st.dataframe(Alpha)

            st.download_button(
                label="Download Gains as CSV",
                data=gains.to_csv(index=False),
                file_name="gains.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Losses as CSV",
                data=losses.to_csv(index=False),
                file_name="losses.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Alpha as CSV",
                data=Alpha.to_csv(index=False),
                file_name="alpha.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
