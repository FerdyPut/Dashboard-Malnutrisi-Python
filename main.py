#Library untuk streamlit dashboard
import streamlit as st
import plotly.express as px
import pandas as pd 
import os
from sklearn.preprocessing import StandardScaler
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
import pyrebase
from datetime import datetime
import re


st.set_page_config(page_title="Dashboard Interaktif - Malnutrisi Indonesia", page_icon=":bar_chart:", layout="wide")

#Configurasi key
firebaseConfig = {
  'apiKey': "AIzaSyCTUXhaO97b3PQxdFu0uj-cbn7ZblO3CcQ",
  'authDomain': "database-malnutrisi.firebaseapp.com",
  'projectId': "database-malnutrisi",
  'databaseURL' : "https://database-malnutrisi-default-rtdb.firebaseio.com/",
  'storageBucket': "database-malnutrisi.appspot.com",
  'messagingSenderId': "313453288601",
  'appId': "1:313453288601:web:d3eae44b8180f1251eac08",
  'measurementId': "G-4CJV8W8WZB"
}

#firebase authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

#Database
db = firebase.database()
storage = firebase.storage()


# Membuat session state untuk menyimpan status login
if 'login_success' not in st.session_state:
    st.session_state.login_success = False

# Tombol Logout di sidebar
if st.session_state.login_success:
    logout = st.sidebar.button('Logout')
    if logout:
        auth.current_user = None  # Logout dari Firebase
        st.session_state.login_success = False  # Set status login kembali ke False
        # Atur ulang halaman atau bagian yang menampilkan elemen-elemen terkait pengguna yang sudah login
        st.experimental_rerun()

# Jika pengguna sudah login, sembunyikan elemen login

if 'handle' not in st.session_state:
    st.session_state.handle = "Anonim"  # Inisialisasi nilai handle jika belum ada

if not st.session_state.login_success:
    choice = st.sidebar.selectbox('Login/Signup', ['Login', 'Sign Up'])
    email = st.sidebar.text_input('Masukkan Email!')
    password = st.sidebar.text_input('Masukkan Password!', type='password')

    if choice == "Sign Up":
        handle_input = st.sidebar.text_input('Masukkan Username', value='Default')
        submit = st.sidebar.button("Buat Akun")

        if submit:
            # Kode lainnya untuk Sign Up
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Email tidak benar!")
            if len(email.strip()) == 0 or len(password.strip()) == 0:
                st.error("Email dan password tidak boleh kosong!")
            else:
                try:
                    # Coba membuat pengguna baru
                    user = auth.create_user_with_email_and_password(email, password)
                    st.success("Akun berhasil dibuat!")
                    st.balloons()

                    # Perbarui nilai handle dengan nilai yang dimasukkan oleh pengguna
                    st.session_state.handle = handle_input

                    # Update status login
                    st.session_state.login_success = False
                
                    # Tampilkan pesan untuk login setelah berhasil membuat akun
                    st.info('Silahkan Login!')

                except:
                    st.error("Email sudah digunakan!")

    elif choice == "Login":

        # Tambahkan space antara kolom masukan password dan tombol login
        st.sidebar.write("")  

        # Tampilkan tombol "Login" di bawah kolom masukan password
        login = st.sidebar.button('Login')

        if login:
            if len(email.strip()) == 0 or len(password.strip()) == 0:
                st.error("Email dan password tidak boleh kosong!")
            elif len(password) < 8:
                st.error("Kata Sandi harus memiliki setidaknya 8 karakter")
            else:
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.success("Login berhasil!")
                    st.session_state.login_success = True  # Update status login
                except:
                    st.error("Kata Sandi/Email yang Anda Masukkan Salah")

# Check status login sebelum menampilkan konten
if st.session_state.login_success:
    #---------------------Memberikan title
    st.title(" :chart_with_upwards_trend: Dashboard Interaktif - Malnutrisi Indonesia ")
    st.markdown(f"<marquee behavior='scroll' direction='left'>SELAMAT DATANG DI DASHBOARD INTERAKTIF <span style='font-size:30px; font-weight: bold;'>{st.session_state.handle}</span></marquee>", unsafe_allow_html=True)


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
    included_variables = [col for col in df.columns if col not in ["Id", "Tahun", "Provinsi", "Longitude", "Latitude"]]


    #------------------------Membuat list untuk variabel kategorikal dan numerik
    kategorikal_vars = []
    numerik_vars = []

    # Loop melalui setiap kolom dalam DataFrame kecuali yang sudah dikecualikan
    for col in included_variables:
        if df[col].dtype == 'object':  # Jika tipe data adalah objek, maka itu kategorikal
            kategorikal_vars.append(col)
        else:  # Jika tidak, itu numerik
            numerik_vars.append(col)


    #Tahun 
    tahun = df['Tahun'].iloc[0]  # Mengambil nilai tahun dari baris pertama DataFrame df
    # Selectbox untuk memilih variabel numerik
    selected_variable = st.sidebar.selectbox(
        "Pilih Variabel Numerik",
        options=numerik_vars,  # Menggunakan daftar variabel numerik
        index=0  # Pilih variabel pertama sebagai nilai default
    )

    # Selectbox untuk memilih variabel kategorikal
    selected_kategorikal_variable = st.sidebar.selectbox(
        "Pilih Variabel Kategorikal",
        options=kategorikal_vars,  # Menggunakan daftar variabel kategorikal
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
    st.markdown(f"<h3 style='color: #124076; font-family: Arial; text-align: center;'>ScoreCard Summary Statistik Malnutrisi Indonesia {tahun}</h3>", unsafe_allow_html=True)
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


    with st.expander(f"OVERVIEW TABEL Malnutrisi Indonesia {tahun} (ketuk untuk melihat tabel) "):
        # Menampilkan DataFrame yang difilter
        st.write(df)

    #-----------------------------------------TABSPANEL
    guide,vis,stat = st.tabs(["Panduan","Visualisasi","Metode Statistika"])
    with guide:
        st.markdown("<h3 style='text-align: center;'>Panduan Dashboard</h3>", unsafe_allow_html=True)
        st.markdown("<h6 style='text-align: center; color: blue'><i class='fa fa-angle-right' style='color: blue'></i> Adapun panduan dashboard ini bertujuan untuk mempermudah akses user dalam penggunaan dashboard</h6>", unsafe_allow_html=True)
        st.markdown("""
            <style>
                .icon {
                    color: purple;
                    margin-right: 5px;
                }
            </style>
            <h6 style='text-align: justify; color: purple'>
                <i class='icon'>→</i> Dibagian kiri terdapat sidebar panel yang merupakan menu dashboard untuk mengganti variabel Malnutrisi yang diinginkan dan terdapat metode statistik yang diinginkan (Normalitas, Regresi, dan Cluster).
            </h6>
        """, unsafe_allow_html=True)
        st.markdown("""
            <style>
                .icon {
                    color: purple;
                    margin-right: 5px;
                }
            </style>
            <h6 style='text-align: justify; color: purple'>
                <i class='icon'>→</i> Di bagian atas terdapat scorecard sebagai summary statistik secara keseluruhan dari variabel-variabel malnutrisi dan juga terdapat overview tabel yang berfungsi sebagai melihat tabel data yang akan digunakan.
            </h6>
        """, unsafe_allow_html=True)
        st.markdown("""
            <style>
                .icon {
                    color: purple;
                    margin-right: 5px;
                }
            </style>
            <h6 style='text-align: justify; color: purple'>
                <i class='icon'>→</i> Terdapat beberapa tab panel yang terdiri dari panduan sebagai tutorial mengakses dashboard, visualisasi sebagai gambaran visual untuk analisis datanya, dan metode statistika sebagai pengujian statistik dari data yang akan dianalisis.
            </h6>
        """, unsafe_allow_html=True)
    with vis:
        st.markdown(f"<h3 style='text-align: center;'>Visualisasi Map Malnutrisi Indonesia {tahun}</h3>", unsafe_allow_html=True)    # Visualisasi peta berdasarkan variabel yang dipilih
        st.markdown("""
            <style>
                .icon {
                    color: blue;
                    margin-right: 5px;
                }
            </style>
            <h6 style='text-align: center; color: blue'>
                <i class='icon'>→</i> Visualisasi disini terdapat visualisasi map untuk kondisi malnutrisi sesuai variabel yang dipilih, visualisasi pie chart terkait pendapatan rata-rata saja, dan visualisasi boxplot untuk data yang sifatnya numerik.
            </h6>
        """, unsafe_allow_html=True)
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
        with st.expander(f"VISUALISASI PIE CHART & BOX PLOT MALNUTRISI INDONESIA {tahun}"):
            pie_chart_column, box_plot_column = st.columns(2)

        # Pie chart berdasarkan variabel kategorikal yang dipilih
        # Menghitung jumlah kemunculan setiap nilai dalam kolom kategorikal yang dipilih
        with pie_chart_column:
            value_counts = df[selected_kategorikal_variable].value_counts()
            fig_pie = px.pie(values=value_counts, names=value_counts.index, title="Persentase " + selected_kategorikal_variable)
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
            st.markdown(f"<h3 style='text-align: center;'> UJI DISTRIBUSI NORMAL</h3>", unsafe_allow_html=True)   
            st.markdown("""
            <style>
                .icon {
                    color: blue;
                    margin-right: 5px;
                }
            </style>
            <h6 style='text-align: center; color: blue'>
                <i class='icon'>→</i> Pengujian distribusi normal adalah pengujian untuk mengukur suatu data apakah mengikuti distribusi normal sesuai teori gaussian dalam statistik atau tidak. Pengujian distribusi normal menggunakan Kolmogorov-Smirnov.
            </h6>
        """, unsafe_allow_html=True)
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
            st.markdown(f"<h3 style='text-align: center;'> UJI REGRESI LINIEAR</h3>", unsafe_allow_html=True)   
            st.markdown("""
            <style>
                .icon {
                    color: blue;
                    margin-right: 5px;
                }
            </style>
            <h6 style='text-align: center; color: blue'>
                <i class='icon'>→</i> Pengujian regresi linier baik sederhana maupun berganda merupakan pengujian untuk mengetahui apakah variabel-variabel X berpengaruh signifikan terhadap variabel Y.
            </h6>
        """, unsafe_allow_html=True)
        # Daftar variabel yang akan dikecualikan
            excluded_variables = ["Id", "Tahun", "Longitude", "Latitude", "Provinsi"]

            # Tambahkan variabel kategorikal yang dipilih ke dalam daftar variabel yang akan dikecualikan
            excluded_variables.append(selected_kategorikal_variable)

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
            st.markdown(f"<h3 style='text-align: center;'> ANALISIS CLUSTER</h3>", unsafe_allow_html=True)   
            st.markdown("""
            <style>
                .icon {
                    color: blue;
                    margin-right: 5px;
                }
            </style>
            <h6 style='text-align: center; color: blue'>
                <i class='icon'>→</i> Analisis Cluster adalah analisis pengelompokkan suatu variabel-variabel yang ada ke dalam klaster-klaster kecil sesuai ciri khas dan kharakteristiknya.
            </h6>
        """, unsafe_allow_html=True)
            # Pilihan variabel yang akan dikecualikan
            excluded_variables = ["Id", "Tahun", "Longitude", "Latitude", "Provinsi"]

            # Ambil daftar kolom yang akan disaring
            included_variables = [col for col in df.select_dtypes(include=['int', 'float']).columns if col not in excluded_variables]
            # Input jumlah cluster
            selected = st.multiselect("Pilih Variabel", included_variables)
            # Menambahkan kolom konstanta untuk model regresi
            selected2 = sm.add_constant(df[selected])
            num_clusters = st.number_input("Masukkan Jumlah k untuk Elbow:", min_value=1, max_value=20, step=1)

            # Memilih variabel independen
            X = selected2.iloc[:, 1:].values
            # Membuat objek scaler
            scaler = StandardScaler()

            # Melakukan standardisasi pada data X
            X_scaled = scaler.fit_transform(X)
            # Membuat model Elbow
            distortion = []
            for i in range(1, num_clusters + 1):
                    kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42)
                    kmeans.fit(X_scaled)
                    distortion.append(kmeans.inertia_)

            with st.expander("Data View +Hasil Standarisasi"):
                st.write(X)
                st.write("Hasil Standarisasi")
                st.write(X_scaled)
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
                    # Find the index of the first distortion that is below 50
                        optimal_k_index = None
                        for i, dist in enumerate(distortions):
                            if dist < 50:
                                optimal_k_index = i
                                break
                        
                        # Optimal k is one more than the index (since indexing starts from 0)
                        if optimal_k_index is not None:
                            return optimal_k_index 
                        else:
                            return len(distortions)  # Return the maximum number of clusters if no point is below 50

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

            #Karakteristik Cluster
            st.markdown("<h4 style='color: black;'>Karakteristik Klaster (Rata-rata)</h4>", unsafe_allow_html=True)
            st.write("<h6 style='color: black; text-align: center;'>Karakteristik klaster yang dilihat dari rata-rata setiap variabelnya. Artinya, provinsi manakah yang cenderung memiliki nilai yang mirip degnan rata-rata setiap klasternya.</h6>", unsafe_allow_html=True)
            # Menjalankan KMeans
            def calculate_cluster_means(selected_data, cluster_column, selected_variables):
                # Menghitung rata-rata berbagai variabel berdasarkan klaster
                cluster_means = selected_data.groupby(cluster_column)[selected_variables].mean().reset_index()

                return cluster_means

            # Menyimpan kolom latitude dan longitude dari DataFrame df
            selected2['Longitude'] = df['Longitude']
            selected2['Latitude'] = df['Latitude']

            # Filter DataFrame berdasarkan variabel yang dipilih
            selected_data = selected2[selected]

            # Menambahkan kolom Klaster ke DataFrame selected_data
            selected_data['Cluster'] = kmeans.labels_
            # Gabungkan DataFrame hasil klasterisasi dengan DataFrame asli untuk mendapatkan informasi provinsi
            clustered_data_with_provinces = pd.merge(selected_data, df[['Provinsi']], left_index=True, right_index=True)
            # Kelompokkan DataFrame berdasarkan klaster
            clustered_provinces = clustered_data_with_provinces.groupby('Cluster')['Provinsi'].apply(list).reset_index(name='Provinsi')
            # Menghitung rata-rata berbagai variabel berdasarkan klaster
            cluster_means = calculate_cluster_means(selected_data, 'Cluster', selected)
            # + provinsi
            cluster_means_with_provinces = pd.merge(cluster_means, clustered_provinces, on='Cluster')

            # Menampilkan hasil
            st.write(cluster_means_with_provinces)
else:
    st.info("Silakan login terlebih dahulu.")
