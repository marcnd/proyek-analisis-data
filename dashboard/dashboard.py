
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# =========================================================
# 1. KONFIGURASI HALAMAN
# =========================================================
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
DAY_FILE = BASE_DIR / "day_clean.csv"
HOUR_FILE = BASE_DIR / "hour_clean.csv"


# =========================================================
# 2. FUNGSI BANTU
# =========================================================
@st.cache_data
def load_data():
    """Membaca data harian dan per jam."""
    day = pd.read_csv(DAY_FILE, parse_dates=["dteday"])
    hour = pd.read_csv(HOUR_FILE, parse_dates=["dteday"])
    return day, hour


def add_calendar_columns(df):
    """Menambahkan label musim, cuaca, tahun, dan kategori cuaca."""
    df = df.copy()

    season_labels = {
        1: "Spring",
        2: "Summer",
        3: "Fall",
        4: "Winter",
    }

    weather_labels = {
        1: "Cerah",
        2: "Berkabut",
        3: "Hujan ringan",
        4: "Hujan deras",
    }

    if "season" in df.columns:
        df["season_name"] = df["season"].map(season_labels)

    if "weathersit" in df.columns:
        df["weather_name"] = df["weathersit"].map(weather_labels)

        df["weather_group"] = df["weathersit"].map(
            lambda x: (
                "Cerah" if x == 1
                else "Cuaca buruk" if x in [3, 4]
                else "Berkabut" if x == 2
                else "Tidak diketahui"
            )
        )

    if "yr" in df.columns:
        df["year_name"] = df["yr"].map({0: "2011", 1: "2012"})

    return df


def format_number(value):
    """Memformat angka menggunakan titik sebagai pemisah ribuan."""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def show_chart(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# =========================================================
# 3. MEMUAT DAN MEMERIKSA DATA
# =========================================================
st.title("Bike Sharing Dashboard")
st.caption(
    "Dashboard penyewaan sepeda tahun 2011–2012 "
    "berdasarkan musim, kondisi cuaca, dan jam."
)

if not DAY_FILE.exists() or not HOUR_FILE.exists():
    st.error(
        "File data tidak ditemukan. Pastikan file berikut berada "
        "dalam folder yang sama dengan dashboard.py:\n\n"
        "- day_clean.csv\n"
        "- hour_clean.csv"
    )
    st.stop()

try:
    day_df, hour_df = load_data()
except Exception as error:
    st.error(f"Data gagal dibaca. Detail: {error}")
    st.stop()

day_df = add_calendar_columns(day_df)
hour_df = add_calendar_columns(hour_df)


required_day_columns = {
    "dteday", "season", "weathersit", "casual",
    "registered", "cnt", "yr"
}
required_hour_columns = {
    "dteday", "hr", "season", "weathersit", "casual",
    "registered", "cnt", "yr"
}

missing_day = required_day_columns - set(day_df.columns)
missing_hour = required_hour_columns - set(hour_df.columns)

if missing_day or missing_hour:
    messages = []

    if missing_day:
        messages.append(
            f"Kolom yang tidak ditemukan di day_clean.csv: "
            f"{', '.join(sorted(missing_day))}"
        )

    if missing_hour:
        messages.append(
            f"Kolom yang tidak ditemukan di hour_clean.csv: "
            f"{', '.join(sorted(missing_hour))}"
        )

    st.error("\n\n".join(messages))
    st.stop()


# =========================================================
# 4. SIDEBAR: NAVIGASI DAN FILTER
# =========================================================
st.sidebar.title("Navigasi")

page = st.sidebar.radio(
    "Pilih halaman:",
    [
        "Ringkasan",
        "Analisis Musim",
        "Analisis Cuaca",
        "Analisis Per Jam",
    ],
)

st.sidebar.divider()
st.sidebar.subheader("Filter Data")

year_options = sorted(day_df["year_name"].dropna().unique().tolist())

selected_years = st.sidebar.multiselect(
    "Tahun",
    options=year_options,
    default=year_options,
)

season_order = ["Spring", "Summer", "Fall", "Winter"]
season_options = [
    season for season in season_order
    if season in day_df["season_name"].dropna().unique()
]

selected_seasons = st.sidebar.multiselect(
    "Musim",
    options=season_options,
    default=season_options,
)

weather_order = ["Cerah", "Berkabut", "Hujan ringan", "Hujan deras"]
weather_options = [
    weather for weather in weather_order
    if weather in hour_df["weather_name"].dropna().unique()
    or weather in day_df["weather_name"].dropna().unique()
]

selected_weather = st.sidebar.multiselect(
    "Kondisi cuaca",
    options=weather_options,
    default=weather_options,
)

st.sidebar.caption(
    "Filter tahun dan musim digunakan pada semua halaman. "
    "Filter cuaca digunakan pada ringkasan dan analisis musim/per jam. "
    "Pada analisis cuaca, perbandingan tetap menggunakan cuaca cerah "
    "dan cuaca buruk (hujan ringan serta hujan deras)."
)


# =========================================================
# 5. FILTER DATA
# =========================================================
filtered_day = day_df[
    day_df["year_name"].isin(selected_years)
    & day_df["season_name"].isin(selected_seasons)
    & day_df["weather_name"].isin(selected_weather)
].copy()

filtered_hour = hour_df[
    hour_df["year_name"].isin(selected_years)
    & hour_df["season_name"].isin(selected_seasons)
    & hour_df["weather_name"].isin(selected_weather)
].copy()

# Filter khusus untuk perbandingan cuaca.
# Filter cuaca sidebar sengaja tidak digunakan di sini.
weather_compare = day_df[
    day_df["year_name"].isin(selected_years)
    & day_df["season_name"].isin(selected_seasons)
    & day_df["weather_group"].isin(["Cerah", "Cuaca buruk"])
].copy()


# =========================================================
# 6. HALAMAN RINGKASAN
# =========================================================
if page == "Ringkasan":
    st.header("Ringkasan Penyewaan Sepeda")
    st.write(
        "Ringkasan jumlah penyewaan berdasarkan filter yang dipilih "
        "pada sidebar."
    )

    if filtered_day.empty:
        st.warning(
            "Tidak ada data yang cocok dengan filter. "
            "Silakan ubah pilihan pada sidebar."
        )
    else:
        total_rentals = filtered_day["cnt"].sum()
        average_daily = filtered_day["cnt"].mean()
        casual_total = filtered_day["casual"].sum()
        registered_total = filtered_day["registered"].sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total penyewaan", format_number(total_rentals))
        col2.metric("Rata-rata per hari", format_number(average_daily))
        col3.metric("Pengguna kasual", format_number(casual_total))
        col4.metric("Pengguna terdaftar", format_number(registered_total))

        st.subheader("Penyewaan Sepeda dari Waktu ke Waktu")

        daily_trend = (
            filtered_day.groupby("dteday", as_index=False)["cnt"]
            .sum()
            .sort_values("dteday")
        )

        fig, ax = plt.subplots(figsize=(12, 4.5))
        ax.plot(
            daily_trend["dteday"],
            daily_trend["cnt"],
            linewidth=1.8,
        )

        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Jumlah penyewaan")
        ax.set_title("Jumlah Penyewaan Sepeda Harian")
        ax.grid(True, alpha=0.25)

        fig.tight_layout()
        show_chart(fig)

        st.markdown(
            "**Insight:** Jumlah penyewaan berubah dari hari ke hari. "
            "Grafik ini dapat digunakan untuk melihat pola kenaikan "
            "dan penurunan penyewaan selama periode yang dipilih."
        )

        st.subheader("Data yang Digunakan")

        c1, c2 = st.columns(2)
        c1.metric("Baris data harian", f"{len(filtered_day):,}".replace(",", "."))
        c2.metric("Baris data per jam", f"{len(filtered_hour):,}".replace(",", "."))


# =========================================================
# 7. HALAMAN ANALISIS MUSIM
# =========================================================
elif page == "Analisis Musim":
    st.header("Analisis Penyewaan Berdasarkan Musim")

    st.write(
        "Pada musim apa rata-rata jumlah penyewaan sepeda harian "
        "paling tinggi selama periode 2011–2012?"
    )

    if filtered_day.empty:
        st.warning(
            "Tidak ada data yang cocok dengan filter. "
            "Silakan ubah pilihan pada sidebar."
        )
    else:
        season_avg = (
            filtered_day.groupby("season_name", as_index=False)["cnt"]
            .mean()
            .rename(columns={"cnt": "average_rentals"})
        )

        season_avg["season_name"] = pd.Categorical(
            season_avg["season_name"],
            categories=season_order,
            ordered=True,
        )
        season_avg = season_avg.sort_values("season_name")

        fig, ax = plt.subplots(figsize=(10, 5))

        bars = ax.bar(
            season_avg["season_name"].astype(str),
            season_avg["average_rentals"],
        )

        ax.set_title("Rata-rata Penyewaan Sepeda Harian per Musim")
        ax.set_xlabel("Musim")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.grid(axis="y", alpha=0.25)
        ax.bar_label(bars, fmt="%.0f", padding=3)

        fig.tight_layout()
        show_chart(fig)

        highest = season_avg.loc[season_avg["average_rentals"].idxmax()]
        lowest = season_avg.loc[season_avg["average_rentals"].idxmin()]

        st.markdown("### Insight")

        st.write(
            f"Rata-rata penyewaan tertinggi terjadi pada musim "
            f"**{highest['season_name']}**, sekitar "
            f"**{format_number(highest['average_rentals'])} penyewaan per hari**. "
            f"Sementara itu, rata-rata terendah terjadi pada musim "
            f"**{lowest['season_name']}**, sekitar "
            f"**{format_number(lowest['average_rentals'])} penyewaan per hari**."
        )


# =========================================================
# 8. HALAMAN ANALISIS CUACA
# =========================================================
elif page == "Analisis Cuaca":
    st.header("Analisis Penyewaan Berdasarkan Cuaca")

    st.write(
        "Bagaimana perbedaan rata-rata penyewaan pengguna kasual "
        "dan pengguna terdaftar antara cuaca cerah dan cuaca buruk, "
        "serta kelompok mana yang mengalami penurunan persentase paling besar?"
    )

    st.caption(
        "Cuaca cerah menggunakan weathersit = 1. "
        "Cuaca buruk menggabungkan weathersit = 3 dan 4. "
        "Kategori berkabut tidak disertakan dalam perbandingan ini."
    )

    if (
        weather_compare.empty
        or set(weather_compare["weather_group"].unique())
        != {"Cerah", "Cuaca buruk"}
    ):
        st.warning(
            "Data untuk kedua kondisi cuaca belum lengkap pada filter ini. "
            "Silakan pilih tahun atau musim lain."
        )
    else:
        weather_avg = (
            weather_compare.groupby("weather_group")[["casual", "registered"]]
            .mean()
            .reindex(["Cerah", "Cuaca buruk"])
        )

        fig, ax = plt.subplots(figsize=(9, 5))

        weather_avg.plot(kind="bar", ax=ax, width=0.72)

        ax.set_title("Rata-rata Penyewaan Berdasarkan Kondisi Cuaca")
        ax.set_xlabel("Kondisi cuaca")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.tick_params(axis="x", rotation=0)
        ax.legend(
            ["Pengguna kasual", "Pengguna terdaftar"],
            title="Kelompok pengguna",
        )
        ax.grid(axis="y", alpha=0.25)

        fig.tight_layout()
        show_chart(fig)

        clear = weather_avg.loc["Cerah"]
        bad_weather = weather_avg.loc["Cuaca buruk"]

        casual_drop = (
            (clear["casual"] - bad_weather["casual"])
            / clear["casual"] * 100
            if clear["casual"] > 0 else float("nan")
        )

        registered_drop = (
            (clear["registered"] - bad_weather["registered"])
            / clear["registered"] * 100
            if clear["registered"] > 0 else float("nan")
        )

        st.subheader("Persentase Penurunan Penyewaan")

        decrease_data = pd.Series({
            "Kasual": casual_drop,
            "Terdaftar": registered_drop,
        })

        fig, ax = plt.subplots(figsize=(7, 4.5))

        bars = ax.bar(
            decrease_data.index,
            decrease_data.values,
        )

        ax.set_title("Persentase Penurunan saat Cuaca Buruk")
        ax.set_xlabel("Kelompok pengguna")
        ax.set_ylabel("Penurunan (%)")
        ax.grid(axis="y", alpha=0.25)
        ax.bar_label(bars, fmt="%.2f%%", padding=3)

        fig.tight_layout()
        show_chart(fig)

        st.markdown("### Insight")

        st.write(
            f"Saat cuaca cerah, rata-rata penyewaan pengguna kasual "
            f"mencapai **{format_number(clear['casual'])}**, sedangkan "
            f"pengguna terdaftar mencapai **{format_number(clear['registered'])}**. "
            f"Saat cuaca buruk, rata-ratanya turun menjadi "
            f"**{format_number(bad_weather['casual'])}** untuk pengguna kasual "
            f"dan **{format_number(bad_weather['registered'])}** "
            f"untuk pengguna terdaftar."
        )

        st.write(
            f"Penurunan pengguna kasual sebesar **{casual_drop:.2f}%**, "
            f"sedangkan pengguna terdaftar sebesar "
            f"**{registered_drop:.2f}%**."
        )


        if pd.notna(casual_drop) and pd.notna(registered_drop):
            if casual_drop > registered_drop:
                st.info(
                    "Pengguna kasual mengalami persentase penurunan "
                    "yang lebih besar saat cuaca buruk."
                )
            elif registered_drop > casual_drop:
                st.info(
                    "Pengguna terdaftar mengalami persentase penurunan "
                    "yang lebih besar saat cuaca buruk."
                )
            else:
                st.info(
                    "Kedua kelompok pengguna mengalami persentase "
                    "penurunan yang sama."
                )


# =========================================================
# 9. HALAMAN ANALISIS PER JAM
# =========================================================
elif page == "Analisis Per Jam":
    st.header("Analisis Penyewaan Berdasarkan Jam")

    st.write(
        "Pada jam berapa rata-rata penyewaan sepeda paling tinggi "
        "dan paling rendah, serta kapan perubahan rata-rata antarjam paling besar?"
    )

    if filtered_hour.empty:
        st.warning(
            "Tidak ada data per jam yang cocok dengan filter. "
            "Silakan ubah pilihan pada sidebar."
        )
    else:
        hourly_avg = (
            filtered_hour.groupby("hr", as_index=False)["cnt"]
            .mean()
            .sort_values("hr")
        )

        st.write("Jumlah baris data per jam:", len(filtered_hour))
        st.write(
            "Rata-rata pukul 16.00:", 
            hourly_avg.loc[hourly_avg["hr"] == 16, "cnt"].values
            )

        # Perubahan dihitung terhadap jam sebelumnya.
        hourly_avg["change"] = hourly_avg["cnt"].diff()

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(
            hourly_avg["hr"],
            hourly_avg["cnt"],
            marker="o",
            linewidth=2,
        )

        ax.set_title("Rata-rata Penyewaan Sepeda pada Setiap Jam")
        ax.set_xlabel("Jam")
        ax.set_ylabel("Rata-rata penyewaan")
        ax.set_xticks(range(24))
        ax.set_xticklabels(
            [f"{hour:02d}.00" for hour in range(24)],
            rotation=45,
        )
        ax.grid(True, alpha=0.25)

        fig.tight_layout()
        show_chart(fig)

        max_row = hourly_avg.loc[hourly_avg["cnt"].idxmax()]
        min_row = hourly_avg.loc[hourly_avg["cnt"].idxmin()]

        # Bandingkan hanya jam berurutan agar tidak keliru
        # jika ada jam yang tidak tersedia setelah filter.
        consecutive_changes = hourly_avg[
            hourly_avg["hr"].diff() == 1
        ].copy()

        if consecutive_changes.empty:
            st.warning(
                "Tidak cukup data dari jam yang berurutan untuk "
                "menghitung perubahan terbesar. Coba ubah filter."
            )
        else:
            consecutive_changes["absolute_change"] = (
                consecutive_changes["change"].abs()
            )

            biggest_change_row = consecutive_changes.loc[
                consecutive_changes["absolute_change"].idxmax()
            ]

            change_hour = int(biggest_change_row["hr"])
            previous_hour = change_hour - 1
            change_value = float(biggest_change_row["change"])

            st.markdown("### Insight")

            st.write(
                f"Rata-rata penyewaan tertinggi terjadi pada pukul "
                f"**{int(max_row['hr']):02d}.00**, sekitar "
                f"**{format_number(max_row['cnt'])} penyewaan**. "
                f"Rata-rata terendah terjadi pada pukul "
                f"**{int(min_row['hr']):02d}.00**, sekitar "
                f"**{format_number(min_row['cnt'])} penyewaan**."
            )

            direction = (
                "kenaikan" if change_value > 0 else "penurunan"
            )

            st.write(
                f"Perubahan rata-rata terbesar terjadi dari pukul "
                f"**{previous_hour:02d}.00** ke **{change_hour:02d}.00**, "
                f"berupa {direction} sekitar "
                f"**{format_number(abs(change_value))} penyewaan**."
            )

        st.subheader("Ringkasan Rata-rata per Jam")

        display_hourly = hourly_avg[
            ["hr", "cnt", "change"]
        ].rename(
            columns={
                "hr": "Jam",
                "cnt": "Rata-rata penyewaan",
                "change": "Perubahan dari jam sebelumnya",
            }
        )

        display_hourly["Jam"] = display_hourly["Jam"].map(
            lambda value: f"{int(value):02d}.00"
        )

        display_hourly["Rata-rata penyewaan"] = (
            display_hourly["Rata-rata penyewaan"].round(2)
        )

        display_hourly["Perubahan dari jam sebelumnya"] = (
            display_hourly["Perubahan dari jam sebelumnya"].round(2)
        )

        st.dataframe(
            display_hourly,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# 10. CATATAN SUMBER DATA
# =========================================================
st.divider()

st.caption(
    "Sumber data: Bike Sharing Dataset (2011–2012). "
    "Hasil analisis mengikuti filter yang dipilih. "
    "Perbandingan cuaca menggunakan kategori cerah (weathersit = 1) "
    "dan cuaca buruk (weathersit = 3 atau 4)."
)
st.caption("Bike Sharing Dashboard | Copyright © Michelle Marcelina 2026")