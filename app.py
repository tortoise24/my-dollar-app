import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 모바일 및 웹 화면 최적화 설정
st.set_page_config(page_title="1년 달러 스마트 감시자", page_icon="📈", layout="centered")

@st.cache_data(ttl=3600)  # 1시간 동안 데이터를 저장하여 속도 향상
def get_usd_history_1y():
    """야후 파이낸스에서 최근 1개년(1y) 원/달러 환율 데이터를 가져오는 함수"""
    try:
        # 원/달러 환율 티커: KRW=X
        ticker = yf.Ticker("KRW=X")
        df = ticker.history(period="1y", interval="1d")
        
        if not df.empty:
            df = df[['Close']].rename(columns={'Close': 'Rate'})
            df.index = pd.to_datetime(df.index)  # 날짜 형식 변환 (시간축 줌인 최적화)
            return df
        return None
    except Exception as e:
        return None

# --- 앱 UI 시작 ---
st.title("📈 1년 기준 달러 분석 & 계산기")
st.caption("최근 1개년 시장 데이터를 자동 분석한 매수 타이밍과 실시간 환전 계산기")

with st.spinner("최근 1년치 환율 데이터를 불러와 분석하는 중..."):
    df_history = get_usd_history_1y()

if df_history is not None and len(df_history) > 0:
    # 1. 1년 데이터 자동 계산 (최저점, 최고점, 평균값, 현재값)
    lowest_limit = float(df_history['Rate'].min())
    highest_limit = float(df_history['Rate'].max())
    average_rate = float(df_history['Rate'].mean())
    current_rate = float(df_history['Rate'].iloc[-1]) # 가장 최신 영업일 종가 기준

    # 2. 상단 메인 지표 표시 (Metric)
    st.subheader("📊 현재 시장 분석 (최근 1년 기준)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="현재 원/달러 환율", value=f"{current_rate:,.1f} 원")
    with col2:
        st.metric(label="1년 평균 환율", value=f"{average_rate:,.1f} 원")

    # 3. 1년 기준 자동 분석 카드 출력
    if current_rate >= highest_limit - 15:
        st.error(f"🚨 **매수 금지 (1년 최고점 부근)**\n현재 환율이 최근 1년 최고점({highest_limit:,.1f}원)에 가깝습니다. 관망하세요!")
    elif current_rate <= lowest_limit + 15:
        st.success(f"✨ **적극 매수 기회 (1년 최저점 부근)**\n현재 환율이 최근 1년 최저점({lowest_limit:,.1f}원) 수준입니다. 달러를 비축하세요!")
    elif current_rate <= average_rate:
        st.info(f"🍏 **분할 매수 추천 (1년 평균 이하)**\n현재 환율이 1년 평균값({average_rate:,.1f}원)보다 낮아 분할 매수하기 좋습니다.")
    else:
        st.warning(f"😐 **관망 또는 소액 환전 (1년 평균 이상)**\n1년 평균 단가({average_rate:,.1f}원)보다는 조금 비싼 편입니다.")

    st.markdown(f"**🔍 최근 1개년 통계 자동 산출 결과**")
    st.text(f"• 1년 최고점: {highest_limit:,.1f}원\n• 1년 최저점: {lowest_limit:,.1f}원\n• 1년 평균점: {average_rate:,.1f}원")

    st.markdown("---")

    # 4. 실시간 환전 계산기 기능
    st.subheader("🧮 실시간 환전 계산기")
    calc_type = st.radio("계산 방식을 선택하세요:", ["원화를 달러로 바꾸기 (KRW ➡️ USD)", "달러를 원화로 바꾸기 (USD ➡️ KRW)"], horizontal=True)

    if calc_type == "원화를 달러로 바꾸기 (KRW ➡️ USD)":
        krw_input = st.number_input("바꿀 원화 금액을 입력하세요 (원)", value=100000, step=10000)
        usd_result = krw_input / current_rate
        st.info(f"💰 **{krw_input:,}원**을 바꾸면 ➡️ **{usd_result:,.2f} 달러($)**가 됩니다.")
    else:
        usd_input = st.number_input("바꿀 달러 금액을 입력하세요 ($)", value=100, step=10)
        krw_result = usd_input * current_rate
        st.info(f"💰 **{usd_input:,} 달러($)**를 바꾸면 ➡️ **{krw_result:,.0f} 원**이 됩니다.")

    st.markdown("---")

    # 5. 1개년 흐름 차트 그리기
    st.subheader("📊 최근 1년 환율 흐름 차트")
    st.caption("💡 마우스 휠이나 차트 우상단 돋보기 아이콘(+/-)으로 확대/축소하면 년 ➡️ 월 ➡️ 주 ➡️ 일 순서로 자동 전환됩니다.")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_history.index, 
        y=df_history['Rate'], 
        mode='lines',
        name='원/달러 환율',
        line=dict(color='#2ca02c', width=2.5),
        fill='tozeroy', 
        fillcolor='rgba(44, 160, 44, 0.1)'
    ))
    
    # 🌟 [해결 팁] 밀리초 단위를 사용해 줌인 강도에 따라 년 -> 월 -> 주 -> 일 포맷 엄격 고정
    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=10),
        height=340,
        hovermode="x unified",
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            type='date',
            tickformatstops=[
                # 1. 줌아웃 (멀리서 전체 볼 때): 연도 표시
                dict(dtickrange=[M12 := 31536000000, None], value="%Y년"),
                # 2. 중간 줌 (몇 달 단위로 볼 때): 월 표시
                dict(dtickrange=[W1 := 604800000, M12], value="%m월"),
                # 3. 더 줌인 (몇 주 단위로 볼 때): 주(Week) 표시
                dict(dtickrange=[D1 := 86400000, W1], value="%U주차"),
                # 4. 최대 줌인 (며칠 단위로 쪼개 볼 때): 일 표시
                dict(dtickrange=[None, D1], value="%d일 (%a)")
            ]
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.1)', 
            automargin=True
        )
    )
    
    # 스트림릿 차트 화면 출력 설정 (도구창 상시 노출 및 스크롤 줌 활성화)
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

else:
    st.error("금융 서버에서 1년 환율 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
