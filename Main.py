import pandas as pd
import streamlit as st

def main():
    # Optional: Configure the page layout and page title
    st.set_page_config(page_title="Roster Updater", layout="wide")

    # Display image at the very top (above the title)
    st.image("Jag Logo.png", width=200)

    # 2. Page Title
    st.title("Alpha Roster Management Web Application")
    st.write("Upload your rosters and decoder, then generate Gains, Losses, and Alpha rosters.")

    # 3. File uploader widgets
    new_roster_file = st.file_uploader("Upload New Roster CSV", type="csv")
    old_roster_file = st.file_uploader("Upload Old Roster CSV", type="csv")
    decoder_file    = st.file_uploader("Upload Decoder CSV",     type="csv")

    # 4. Button to process data
    if st.button("Generate Gains/Losses/Alpha"):
        # Ensure all three files are uploaded
        if not (new_roster_file and old_roster_file and decoder_file):
            st.warning("Please upload all three CSV files before proceeding.")
        else:
            # --- Read Data ---
            Roster_new = pd.read_csv(new_roster_file, dtype={"DODID": str})  # Ensure DODID is a string
            Roster_old = pd.read_csv(old_roster_file, dtype={"DODID": str})  # Prevents commas in large numbers
            Decode     = pd.read_csv(decoder_file)

            # --- Remove duplicates by DODID ---
            Roster_new = Roster_new.drop_duplicates(subset="DODID")
            Roster_old = Roster_old.drop_duplicates(subset="DODID")

            # --- Select and rename columns as needed ---
            rename_dict = {
                "First Name":       "First",
                "Last Name":        "Last",
                "Birthdate":        "DOB",
                "Email Address":    "Email",
                "Current Rank":     "Rank",
                "Soldier Home UIC": "UIC",
            }
            needed_cols = list(rename_dict.keys()) + ["DODID"]

            Roster_new = (
                Roster_new[needed_cols]
                .rename(columns=rename_dict)
                .assign(
                    First=lambda df: df["First"].astype(str).fillna("").apply(lambda x: x.title() if x else ""),
                    Last=lambda df: df["Last"].astype(str).fillna("").apply(lambda x: x.title() if x else "")
                )
            )
            Roster_old = (
                Roster_old[needed_cols]
                .rename(columns=rename_dict)
                .assign(
                    First=lambda df: df["First"].astype(str).fillna("").apply(lambda x: x.title() if x else ""),
                    Last=lambda df: df["Last"].astype(str).fillna("").apply(lambda x: x.title() if x else "")
                )
            )

            # --- Ensure "UIC" is a string in all datasets before merging ---
            Roster_new["UIC"] = Roster_new["UIC"].astype(str).str.strip()
            Roster_old["UIC"] = Roster_old["UIC"].astype(str).str.strip()
            Decode["UIC"] = Decode["UIC"].astype(str).str.strip()

            # --- Merge Decode onto Rosters ---
            Roster_new = Roster_new.merge(Decode, on="UIC", how="left")
            Roster_old = Roster_old.merge(Decode, on="UIC", how="left")

            # --- Finding missing UICs ---
            UICs = Roster_new[Roster_new['Group'].isna()]
            UICs.to_csv("UICs.csv", index=False)

            # --- Gains & Losses ---
            merge_cols = ["DODID", "First", "Last"]
            gains_mask  = ~Roster_new[merge_cols].apply(tuple, axis=1).isin(
                            Roster_old[merge_cols].apply(tuple, axis=1)
                          )
            losses_mask = ~Roster_old[merge_cols].apply(tuple, axis=1).isin(
                            Roster_new[merge_cols].apply(tuple, axis=1)
                          )
            gains  = Roster_new.loc[gains_mask].copy()
            losses = Roster_old.loc[losses_mask].copy()

            # --- Alpha Roster (Now Includes UIC) ---
            columns_for_alpha = []
            if "CTB" in Roster_new.columns:
                columns_for_alpha.append("CTB")
            if "BN" in Roster_new.columns:
                columns_for_alpha.append("BN")

            Alpha = pd.DataFrame({
                "About": Roster_new["Last"] + " " + Roster_new["First"],
                "DODID": Roster_new["DODID"],
                "Rank":  Roster_new["Rank"],
                "UIC":   Roster_new["UIC"]  # Now includes UIC
            })
            for col in columns_for_alpha:
                Alpha[col] = Roster_new[col]

            # 5. Show results
            st.subheader("Gains")
            st.dataframe(gains)

            st.subheader("Losses")
            st.dataframe(losses)

            st.subheader("Alpha Roster")
            st.dataframe(Alpha)

            # 6. Download buttons (DODID formatted properly)
            st.download_button(
                label="Download Gains as CSV",
                data=gains.to_csv(index=False, quoting=3),  # Ensures DODID does not have commas
                file_name="gains.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Losses as CSV",
                data=losses.to_csv(index=False, quoting=3),  # Ensures DODID does not have commas
                file_name="losses.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Alpha as CSV",
                data=Alpha.to_csv(index=False, quoting=3),  # Ensures DODID does not have commas
                file_name="alpha.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Missing UICs as CSV",
                data=UICs.to_csv(index=False, quoting=3),  # Ensures DODID does not have commas
                file_name="UICs.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
