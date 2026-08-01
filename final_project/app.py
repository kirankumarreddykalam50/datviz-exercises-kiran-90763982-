import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Alias for older Streamlit versions lacking st.columns
if not hasattr(st, "columns"):
    st.columns = st.beta_columns

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Global Gaming Industry Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. DATA LOADING & PREPROCESSING (DYNAMIC RELATIVE PATH)
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "Video_Games.csv")

df = pd.read_csv(CSV_PATH)

if "index" in df.columns:
    df = df.drop(columns=["index"])

df["User_Score"] = pd.to_numeric(df["User_Score"], errors="coerce")
df["Year_of_Release"] = pd.to_numeric(df["Year_of_Release"], errors="coerce")
df["Critic_Score_Scaled"] = df["Critic_Score"] / 10.0
df["Score_Gap"] = df["User_Score"] - df["Critic_Score_Scaled"]


def categorize_platform(plat):
    if plat in ["PS", "PS2", "PS3", "PS4", "PSP", "PSV"]:
        return "PlayStation"
    elif plat in ["X360", "XB", "XOne"]:
        return "Xbox"
    elif plat in [
        "N64",
        "GC",
        "Wii",
        "WiiU",
        "GB",
        "GBA",
        "DS",
        "3DS",
        "NES",
        "SNES",
    ]:
        return "Nintendo"
    elif plat == "PC":
        return "PC"
    else:
        return "Others"


df["Ecosystem"] = df["Platform"].apply(categorize_platform)

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & FILTERS
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Global Dashboard Filters")

min_year = int(df["Year_of_Release"].min())
max_year = int(df["Year_of_Release"].max())

year_range = st.sidebar.slider(
    "Select Year Range:",
    min_value=min_year,
    max_value=max_year,
    value=(1990, max_year),
)

all_genres = sorted([g for g in df["Genre"].dropna().unique()])
selected_genres = st.sidebar.multiselect(
    "Select Genres:", options=all_genres, default=all_genres
)

all_ecosystems = sorted([e for e in df["Ecosystem"].unique()])
selected_ecosystems = st.sidebar.multiselect(
    "Select Hardware Ecosystems:",
    options=all_ecosystems,
    default=all_ecosystems,
)

# Filter Dataframe based on sidebar choices
filtered_df = df[
    (df["Year_of_Release"] >= year_range[0])
    & (df["Year_of_Release"] <= year_range[1])
    & (df["Genre"].isin(selected_genres))
    & (df["Ecosystem"].isin(selected_ecosystems))
]

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD CONTENT & NAVIGATION
# -----------------------------------------------------------------------------
st.markdown(
    '<div class="main-header">🎮 Global Gaming Industry Analytics Dashboard</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Interactive Exploration of Video Game Sales, Reception Metrics, and Ecosystem Dynamics</div>',
    unsafe_allow_html=True,
)

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**Total Games Analyzed**")
    st.subheader(f"{len(filtered_df):,}")

with col2:
    st.markdown("**Total Global Sales**")
    st.subheader(f"{filtered_df['Global_Sales'].sum():,.2f}M Units")

with col3:
    avg_critic = filtered_df["Critic_Score"].mean()
    st.markdown("**Avg Critic Score**")
    st.subheader(f"{avg_critic:.1f} / 100" if pd.notnull(avg_critic) else "N/A")

with col4:
    avg_user = filtered_df["User_Score"].mean()
    st.markdown("**Avg User Score**")
    st.subheader(f"{avg_user:.1f} / 10" if pd.notnull(avg_user) else "N/A")

st.markdown("---")

# Navigation choice compatible with older Streamlit versions
tab_choice = st.radio(
    "Select View:",
    [
        "📊 Market & Sales Trends",
        "🎮 Ecosystem Dynamics",
        "🏆 Publisher Performance",
        "⭐ Perception & Ratings",
    ],
)

# -----------------------------------------------------------------------------
# VIEW 1: Market & Sales Trends
# -----------------------------------------------------------------------------
if tab_choice == "📊 Market & Sales Trends":
    st.subheader("Global & Regional Sales Evolution")

    yearly_sales = (
        filtered_df.groupby("Year_of_Release")[
            ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
        ]
        .sum()
        .reset_index()
    )
    fig_line = px.line(
        yearly_sales,
        x="Year_of_Release",
        y=["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"],
        title="Regional Sales Over Time (Millions of Units)",
        labels={
            "value": "Sales (Millions)",
            "Year_of_Release": "Release Year",
            "variable": "Region",
        },
        template="plotly_white",
    )
    st.plotly_chart(fig_line, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        genre_sales = (
            filtered_df.groupby("Genre")["Global_Sales"]
            .sum()
            .reset_index()
            .sort_values(by="Global_Sales", ascending=False)
        )
        fig_genre = px.bar(
            genre_sales,
            x="Global_Sales",
            y="Genre",
            orientation="h",
            title="Total Global Sales by Genre",
            labels={"Global_Sales": "Global Sales (Millions)", "Genre": "Genre"},
            color="Global_Sales",
            color_continuous_scale="Viridis",
            template="plotly_white",
        )
        fig_genre.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_genre, use_container_width=True)

    with col_b:
        regional_totals = pd.DataFrame(
            {
                "Region": ["North America", "Europe", "Japan", "Other"],
                "Sales": [
                    filtered_df["NA_Sales"].sum(),
                    filtered_df["EU_Sales"].sum(),
                    filtered_df["JP_Sales"].sum(),
                    filtered_df["Other_Sales"].sum(),
                ],
            }
        )
        fig_pie = px.pie(
            regional_totals,
            names="Region",
            values="Sales",
            title="Global Market Share by Region",
            hole=0.4,
            template="plotly_white",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# -----------------------------------------------------------------------------
# VIEW 2: Ecosystem Dynamics
# -----------------------------------------------------------------------------
elif tab_choice == "🎮 Ecosystem Dynamics":
    st.subheader("Platform and Ecosystem Breakdown")

    col_c, col_d = st.columns(2)

    with col_c:
        platform_sales = (
            filtered_df.groupby("Platform")["Global_Sales"]
            .sum()
            .reset_index()
            .sort_values(by="Global_Sales", ascending=False)
            .head(15)
        )
        fig_platform = px.bar(
            platform_sales,
            x="Platform",
            y="Global_Sales",
            title="Top 15 Gaming Platforms by Global Sales",
            labels={
                "Global_Sales": "Global Sales (Millions)",
                "Platform": "Platform",
            },
            color="Global_Sales",
            color_continuous_scale="Blues",
            template="plotly_white",
        )
        st.plotly_chart(fig_platform, use_container_width=True)

    with col_d:
        eco_sales = (
            filtered_df.groupby(["Year_of_Release", "Ecosystem"])[
                "Global_Sales"
            ]
            .sum()
            .reset_index()
        )
        fig_eco_area = px.area(
            eco_sales,
            x="Year_of_Release",
            y="Global_Sales",
            color="Ecosystem",
            title="Hardware Ecosystem Market Share Evolution",
            labels={
                "Global_Sales": "Global Sales (Millions)",
                "Year_of_Release": "Release Year",
            },
            template="plotly_white",
        )
        st.plotly_chart(fig_eco_area, use_container_width=True)

# -----------------------------------------------------------------------------
# VIEW 3: Publisher Performance
# -----------------------------------------------------------------------------
elif tab_choice == "🏆 Publisher Performance":
    st.subheader("Leading Publishers & Top Titles")

    top_publishers = (
        filtered_df.groupby("Publisher")["Global_Sales"]
        .sum()
        .reset_index()
        .sort_values(by="Global_Sales", ascending=False)
        .head(10)
    )
    fig_pub = px.bar(
        top_publishers,
        x="Publisher",
        y="Global_Sales",
        title="Top 10 Publishers by Total Sales Volume",
        labels={
            "Global_Sales": "Global Sales (Millions)",
            "Publisher": "Publisher",
        },
        color="Global_Sales",
        color_continuous_scale="Teal",
        template="plotly_white",
    )
    st.plotly_chart(fig_pub, use_container_width=True)

    top_games = filtered_df.sort_values(
        by="Global_Sales", ascending=False
    ).head(10)
    fig_games = px.bar(
        top_games,
        x="Global_Sales",
        y="Name",
        color="Platform",
        orientation="h",
        title="Top 10 Best-Selling Video Games of All Time",
        labels={
            "Global_Sales": "Global Sales (Millions)",
            "Name": "Game Title",
        },
        template="plotly_white",
    )
    fig_games.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_games, use_container_width=True)

# -----------------------------------------------------------------------------
# VIEW 4: Perception & Ratings
# -----------------------------------------------------------------------------
elif tab_choice == "⭐ Perception & Ratings":
    st.subheader("Critic vs. User Ratings Analysis")

    scatter_df = filtered_df.dropna(
        subset=["Critic_Score_Scaled", "User_Score"]
    )

    fig_scatter = px.scatter(
        scatter_df,
        x="Critic_Score_Scaled",
        y="User_Score",
        color="Rating",
        size="Global_Sales",
        hover_name="Name",
        labels={
            "Critic_Score_Scaled": "Critic Score (0-10)",
            "User_Score": "User Score (0-10)",
        },
        template="plotly_white",
        opacity=0.7,
    )

    fig_scatter.add_trace(
        go.Scatter(
            x=[0, 10],
            y=[0, 10],
            mode="lines",
            name="Perfect Agreement",
            line=dict(color="gray", dash="dash"),
        )
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")
st.caption("Data Visualization Summer 2026 Course Project")