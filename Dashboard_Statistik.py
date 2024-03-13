#Library untuk streamlit dashboard
import streamlit as st
import plotly.express as px
import pandas as pd 
import os
import warnings
from streamlit_option_menu import option_menu
from numerize.numerize import numerize
import time
import statsmodels.api as sm
import streamlit_extras
from scipy import stats
import numpy as np
import plotly.graph_objs as go
warnings.filterwarnings('ignore')
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn
import threadpoolctl
from sklearn.cluster import KMeans
import plotly.graph_objects as go
import openpyxl


st.set_page_config(page_title="Dashboard Interactive", page_icon=":bar_chart:", layout="wide")
#---------------------Memberikan title
st.title(" :chart_with_upwards_trend: Dashboard Interaktif")

st.markdown('<style>div.block-container{padding-top:lrem;}</style>', unsafe_allow_html=True)
#---------------------Menambahkan file upload
f1 = st.file_uploader("Masukkan File",type =(["csv","txt","xlsx","xls"])) 
if f1 is not None:
    filename = f1.name
    st.write(filename)
    
    # Cek tipe file yang diunggah
    if filename.endswith('.csv'):
        use_header = st.checkbox("Gunakan Header CSV")
        if use_header:
            df = pd.read_csv(f1, sep=',')  # Jika format file adalah .csv dan menggunakan header
        else:
            df = pd.read_csv(f1, sep=',', header=None)  # Jika format file adalah .csv dan tanpa header
    else:
        df = pd.read_excel(f1)

    st.success('File berhasil diunggah!')
else:
    st.warning("Masukkan file terlebih dahulu")

    #KALAU DI GITHUB PAKAI 
    #url = "https://raw.githubusercontent.com/FerdyPut/Dashboard-Malnutrisi/main/Data R.xlsx"
    #df = pd.read_excel(url)

#SIDEBAR PANEL
st.sidebar.markdown("📘Menu Dashboard")
# Daftar variabel yang ingin disertakan dalam select box
included_variables = [col for col in df.columns if col not in ["Id", "Tahun", "Provinsi", "Longitude", "Latitude", "Tingkat Pendapatan Rata rata"]]

# Selectbox untuk memilih variabel tunggal
selected_variable = st.sidebar.selectbox(
    "Pilih Variabel Malnutrisi",
    options=included_variables,  # Menggunakan daftar variabel yang disertakan
    index=0  # Pilih variabel pertama sebagai nilai default
)

# Filter DataFrame based on selected variable
filtered_df = df[selected_variable]


selected_variable2 = st.sidebar.selectbox(
    "Pilih Pengujian",
    options=("","Normalitas","Regression", "Cluster"),  # Menggunakan daftar variabel yang disertakan
    index=0  # Pilih variabel pertama sebagai nilai default
)
#---------------------------Scorecard

# Hitung statistik
rata_rata = df[selected_variable].mean()
total = df[selected_variable].sum()
nilai_max = df[selected_variable].max()
nilai_min = df[selected_variable].min()
    
# Format nilai dengan dua digit desimal
rata_rata_formatted = "{:.2f}".format(rata_rata)
total_formatted = "{:.2f}".format(total)
nilai_max_formatted = "{:.2f}".format(nilai_max)
nilai_min_formatted = "{:.2f}".format(nilai_min)

# Menampilkan statistik dalam ekspander
st.markdown("<h3 style='color: #124076; font-family: Arial; text-align: center;'>ScoreCard Summary Statistik</h3>", unsafe_allow_html=True)
total1, total2, total3, total4 = st.columns(4)
with total1:
        st.info('Rata-rata', icon="📇")
        st.metric(label=f"Variabel {selected_variable}", value=rata_rata_formatted)

with total2:
        st.info('Nilai Maksimum', icon="📇")
        st.metric(label=f"Variabel {selected_variable}", value=nilai_max_formatted)

with total3:
        st.info('Nilai Minimum', icon="💰")
        st.metric(label=f"Variabel {selected_variable}", value=nilai_min_formatted)

with total4:
        st.info('Total', icon="💰")
        st.metric(label=f"Variabel {selected_variable}", value=total_formatted)


with st.expander("OVERVIEW TABEL (ketuk untuk melihat tabel)"):
    # Menampilkan DataFrame yang difilter
    st.write(df)

#-----------------------------------------TABSPANEL
guide,vis,stat = st.tabs(["Panduan","Visualisasi","Metode Statistika"])
with guide:
    st.markdown("<h3 style='text-align: center;'>Panduan Dashboard</h3>", unsafe_allow_html=True)
with vis:
    st.markdown("<h3 style='text-align: center;'>Visualisasi Map Malnutrisi Indonesia 2022</h3>", unsafe_allow_html=True)
    # Visualisasi peta berdasarkan variabel yang dipilih
    fig = px.scatter_mapbox(df, lat="Latitude", lon="Longitude", hover_name="Provinsi", hover_data=[selected_variable],
                            color=selected_variable, size=selected_variable, zoom=3, height=400, width = 930)  # Menggunakan selected_variable sebagai size
    fig.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=[
            {
                "below": 'traces',
                "sourcetype": "raster",
                "sourceattribution": "United States Geological Survey",
                "source": [
                    "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                ]
            }
        ],
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    # Menampilkan peta dalam aplikasi Streamlit
    st.plotly_chart(fig)

    # Visualisasi Pie Chart dan Box Plot
    with st.expander("VISUALISASI PIE CHART & BOX PLOT"):
        pie_chart_column, box_plot_column = st.columns(2)

        # Pie chart berdasarkan kolom "Tingkat Pendapatan Rata-rata"
        # Menghitung jumlah kemunculan setiap nilai dalam kolom "Tingkat Pendapatan Rata-rata"
        with pie_chart_column:
            value_counts = df["Tingkat Pendapatan Rata rata"].value_counts()
            fig_pie = px.pie(values=value_counts, names=value_counts.index, title="Persentase Tingkat Pendapatan Rata rata")
            st.plotly_chart(fig_pie, use_container_width=True)  # Gunakan width yang sama dengan container

        # Visualisasi box plot untuk setiap variabel
        with box_plot_column:
            fig_box = px.box(df[selected_variable], title="Box Plot untuk Variabel " + selected_variable)
            st.plotly_chart(fig_box, use_container_width=True)  # Gunakan width yang sama dengan container

#---------------------Metode Statistika
with stat:
    def kolmogorov_smirnov_test(data):
        # Lakukan uji normalitas Kolmogorov-Smirnov
        kstest_result = stats.kstest(data, 'norm')
        return kstest_result

    # Tombol untuk melakukan uji normalitas jika variabel dipilih adalah "Normalitas"
    if selected_variable2 == "Normalitas":
        data_to_test = df[selected_variable].values
        
        # Melakukan uji normalitas Kolmogorov-Smirnov
        kstest_result = kolmogorov_smirnov_test(data_to_test)

        # Menampilkan hasil uji normalitas
        st.markdown("<h4 style='color: black;'>Hasil Pengujian Normalitas 🔎:</h4>", unsafe_allow_html=True)
        with st.expander("Hasil"):
            st.write("Hasil Uji Normalitas Kolmogorov-Smirnov untuk Variabel", selected_variable)
            st.write("Nilai Kolmogorov Smirnov 💡:", kstest_result.statistic)
            st.write("Nilai P-value 💡:", kstest_result.pvalue)
        st.markdown("<h4 style='color: black;'>Kesimpulan / Interpretasi 🔎:</h4>", unsafe_allow_html=True)
        with st.expander("Simpulan"):
            # Interpretasi hasil uji normalitas
            alpha = 0.05
            if kstest_result.pvalue > alpha:
                st.write("Tidak cukup bukti untuk menolak hipotesis nol (data terdistribusi normal)")
            else:
                st.write("Hipotesis nol ditolak, data tidak terdistribusi normal")
    if selected_variable2 == "Regression":
        # Daftar variabel yang akan dikecualikan
        excluded_variables = ["Id", "Tahun", "Tingkat Pendapatan Rata rata", "Longitude", "Latitude", "Provinsi"]

        # Ambil daftar kolom yang akan disaring
        included_variables = [col for col in df.columns if col != selected_variable
                            and col not in excluded_variables]

        # Multi-select untuk memilih variabel independen (X)
        selected_independent_variables = st.multiselect("Pilih Variabel Independen (X)", included_variables)
        # Menambahkan kolom konstanta untuk model regresi
        X = sm.add_constant(df[selected_independent_variables])

        # Variabel dependen
        Y = df[selected_variable]

        # Membuat model regresi
        model = sm.OLS(Y, X).fit()

        # Menampilkan hasil regresi
        st.markdown("<h4 style='color: black;'>Hasil Pengujian Regresi 🔎:</h4>", unsafe_allow_html=True)
        with st.expander("Hasil"):
            st.write("Hasil Regresi Berganda:")
            st.write(model.summary())

    if selected_variable2 == "Cluster":
        # Pilihan variabel yang akan dikecualikan
        excluded_variables = ["Id", "Tahun", "Tingkat Pendapatan Rata rata", "Longitude", "Latitude", "Provinsi"]

        # Ambil daftar kolom yang akan disaring
        included_variables = [col for col in df.select_dtypes(include=['int', 'float']).columns if col not in excluded_variables]
        # Input jumlah cluster
        selected = st.multiselect("Pilih Variabel", included_variables)
        # Menambahkan kolom konstanta untuk model regresi
        selected2 = sm.add_constant(df[selected])
        num_clusters = st.number_input("Masukkan Jumlah Cluster:", min_value=1, max_value=20, step=1)

        # Memilih variabel independen
        X = selected2.iloc[:, 1:].values
        # Membuat model Elbow
        distortion = []
        for i in range(1, num_clusters + 1):
                kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42)
                kmeans.fit(X)
                distortion.append(kmeans.inertia_)

        with st.expander("Data View"):
            st.write(X)
        # Menampilkan hasil Elbow
        st.markdown("<h4 style='color: black;'>Hasil Elbow </h4>", unsafe_allow_html=True)
        with st.expander("Hasil"):
                st.write("Elbow method menunjukkan bahwa untuk menentukan jumlah k optimum yang nantinya untuk proses analisis klaster")
                # Tampilkan plot Elbow
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(range(1, num_clusters + 1)), y=distortion, mode='lines+markers'))
                fig.update_layout(title='The Elbow Method',
                                xaxis_title='Number of Cluster',
                                yaxis_title='Distortion')
                st.plotly_chart(fig, use_container_width=True)
                # Find the optimal k

                def find_optimal_k(distortions):
                    # Calculate the differences in distortions
                    differences = [distortions[i] - distortions[i+1] for i in range(len(distortions)-1)]
                    # Find the index of the maximum difference
                    optimal_k_index = differences.index(max(differences))
                    # Optimal k is one more than the index (since indexing starts from 0)
                    return optimal_k_index + 1

                optimal_k = find_optimal_k(distortion)
                st.write(f"Jumlah klaster optimal (k) berdasarkan metode Elbow adalah: {optimal_k}")
        #Menampilkan Klaster
        # Visualisasi menggunakan Plotly Express
        st.markdown("<h4 style='color: black;'>Visualisasi Cluster Dengan Map</h4>", unsafe_allow_html=True)
        with st.expander("Visualisasi"):
            k = st.number_input(label = "Masukkan Cluster dari hasil Elbow (k)!")
            k_opt = int(k)
            #modeling
            kmeans = KMeans(n_clusters= k_opt, random_state= 42)
            y_kmeans = kmeans.fit_predict(X)
            #geo map klaster visualisasi
            X = df[['Longitude', 'Latitude']]
            df['Cluster'] = kmeans.labels_
            fig = px.scatter_mapbox(df, lat="Latitude", lon="Longitude", color="Cluster", size="Cluster", zoom=3, height=600)
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig, use_container_width=True)

