    # 以下為用seaborne繪製時序失敗的嘗試
    # plt.ion()
    # plt.close('all')
    # for itemname in itemnames[2:3]:
    #     df_tmp = df1[df1['itemname'] == itemname]
    #     df_tmp.set_index('sampledate2', inplace=True)
    #     df_monthly = df_tmp.groupby(['sitename', 'itemunit']).resample('M').agg({
    #         'itemvalue': 'mean',  # 對 'itemvalue' 進行平均
    #     }).reset_index()

    #     date_range = pd.date_range(start='2020-01-01', end='2023-06-30', freq='M')

    #     # 对每个群组应用 resample
    #     df_filled = []
    #     for (sitename, itemunit), group in df_monthly.groupby(['sitename', 'itemunit']):
    #         group.set_index('sampledate2', inplace=True)
    #         group = group.reindex(date_range).reset_index().rename(columns={'index': 'sampledate2'})
    #         group['sitename'] = group['sitename'].fillna(sitename)
    #         group['itemunit'] = group['itemunit'].fillna(itemunit)
    #         df_filled.append(group)

    #     # 合并所有的数据
    #     df_monthly = pd.concat(df_filled).reset_index(drop=True)
    #     # tmp = df_monthly[df_monthly.sitename == '五空橋']
    #     fig, ax = plt.subplots(figsize=(14, 4))  # 使用 subplots 來取得 ax，以便我們可以在圖上添加網格
    #     sns.pointplot(data=df_monthly, x= 'sampledate2', y='itemvalue', hue='sitename', ax=ax)
    #     # sns.lineplot(data=tmp, x= 'sampledate2', y='itemvalue', hue='sitename', ax=ax, markers=True)
    #     # sns.lineplot(data=df_monthly, x= 'sampledate2', y='itemvalue', hue='sitename', ax=ax, markers=True)

    #     ax.grid(True, linestyle='--', color='black')  # 添加網格線，設定線型為虛線，顏色為黑色
    #     # -- 如果是用lineplot，則要用下面這段設定範圍
    #     # start_date = mdates.date2num(pd.to_datetime('2020-01-01'))
    #     # end_date = mdates.date2num(pd.to_datetime('2023-06-30'))
    #     # ax.set_xlim([start_date, end_date])
    #     ax.set_ylabel(df_tmp['itemunit'].iloc[0])
    #     ax.set_title(f'{itemname} 時序圖')

    #     fig_path = 'images/時序圖/'
    #     if not os.path.exists(fig_path):
    #         os.makedirs(fig_path)
    #     fig.savefig(f'{fig_path}/{itemname}.png', dpi=300)  # 存檔，並設定解析度為 300 dpi