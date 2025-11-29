import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Global Research Impact Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('publications.csv')
    df['Weighted_CNCI'] = df['Category Normalized Citation Impact'] * df['Web of Science Documents']
    return df

df = load_data()

st.sidebar.header("Filter Options")

min_year, max_year = int(df['year'].min()), int(df['year'].max())
selected_years = st.sidebar.slider("Select Year Range", min_year, max_year, (min_year, max_year))

all_countries = sorted(df['Name'].unique())
selected_countries = st.sidebar.multiselect("Select Countries", all_countries, default=all_countries[:5])

mask = (df['year'].between(selected_years[0], selected_years[1])) & (df['Name'].isin(selected_countries))
filtered_df = df[mask]

country_year_agg = filtered_df.groupby(['Name', 'year']).agg({
    'Web of Science Documents': 'sum',
    'Times Cited': 'sum',
    'Weighted_CNCI': 'sum',
    'Documents in Top 1%': 'sum'
}).reset_index()

country_year_agg['Avg CNCI'] = country_year_agg['Weighted_CNCI'] / country_year_agg['Web of Science Documents']

st.title("Global Research Trends: Quantity vs. Quality")
st.markdown("Explore the evolution of scientific output and impact across nations. "
            "This dashboard visualizes the trade-offs between **Research Volume** and **Citation Impact**.")

col1, col2, col3, col4 = st.columns(4)
total_docs = filtered_df['Web of Science Documents'].sum()
avg_impact = (filtered_df['Weighted_CNCI'].sum() / total_docs) if total_docs > 0 else 0
top_country = country_year_agg.groupby('Name')['Web of Science Documents'].sum().idxmax() if not country_year_agg.empty else "N/A"

col1.metric("Total Documents", f"{total_docs:,.0f}")
col2.metric("Avg Citation Impact (CNCI)", f"{avg_impact:.2f}")
col3.metric("Top Producer", top_country)
col4.metric("Active Entities", filtered_df['Name'].nunique())

st.divider()


tab1, tab2, tab3 = st.tabs(["Trends & Evolution", "Impact Matrix", "Elite Performance"])
with tab1:
    st.subheader("Temporal Evolution of Research Output")
    c1, c2 = st.columns(2)
    fig_vol = px.line(country_year_agg, x='year', y='Web of Science Documents', color='Name',
                        title="Growth in Research Volume", markers=True)
    fig_vol.update_layout(xaxis_title="Year", yaxis_title="Documents")
    c1.plotly_chart(fig_vol, use_container_width=True)
    fig_qual = px.line(country_year_agg, x='year', y='Avg CNCI', color='Name',
                        title="Evolution of Citation Impact (CNCI)", markers=True)
    fig_qual.update_layout(xaxis_title="Year", yaxis_title="Category Normalized Citation Impact")
    c2.plotly_chart(fig_qual, use_container_width=True)
with tab2:
    st.subheader("The Efficiency Frontier: Volume vs. Impact")
    st.markdown("Is bigger better? This chart compares the size of output against its normalized impact. "
                "Countries in the **top-left** are 'High Efficiency' (High Impact, Lower Volume).")
    scatter_agg = filtered_df.groupby('Name').agg({
        'Web of Science Documents': 'sum',
        'Weighted_CNCI': 'sum',
        'Documents in Top 1%': 'sum'
    }).reset_index()
    scatter_agg['Overall CNCI'] = scatter_agg['Weighted_CNCI'] / scatter_agg['Web of Science Documents']
    
    fig_bubble = px.scatter(scatter_agg, 
                            x='Web of Science Documents', 
                            y='Overall CNCI',
                            size='Documents in Top 1%', 
                            color='Name',
                            hover_name='Name',
                            title="Impact Matrix (Bubble Size = # of Elite Papers)",
                            labels={'Overall CNCI': 'Avg Citation Impact', 'Web of Science Documents': 'Total Documents'})
    avg_x = scatter_agg['Web of Science Documents'].mean()
    avg_y = scatter_agg['Overall CNCI'].mean()
    fig_bubble.add_vline(x=avg_x, line_dash="dash", line_color="gray", annotation_text="Avg Volume")
    fig_bubble.add_hline(y=avg_y, line_dash="dash", line_color="gray", annotation_text="Avg Impact")
    
    st.plotly_chart(fig_bubble, use_container_width=True)

with tab3:
    st.subheader("The Elite Club: Leadership in Top 1% Papers")
    scatter_agg['% Elite'] = (scatter_agg['Documents in Top 1%'] / scatter_agg['Web of Science Documents']) * 100
    scatter_agg = scatter_agg.sort_values(by='% Elite', ascending=False)
    
    fig_bar = px.bar(scatter_agg, x='Name', y='% Elite', color='% Elite',
                        title="Percentage of Documents in the Global Top 1%",
                        color_continuous_scale='Viridis')
    fig_bar.update_layout(xaxis_title="Country", yaxis_title="% Documents in Top 1%")
    st.plotly_chart(fig_bar, use_container_width=True)
with st.expander("View Raw Data Analysis"):
    st.dataframe(country_year_agg.style.background_gradient(subset=['Avg CNCI'], cmap='Greens'))