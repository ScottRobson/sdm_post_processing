import pandas
import matplotlib.pyplot as plt


def get_graph_plot_arrays(excel_file_path, string_to_search, variance):

    dut_signaling = pandas.read_excel(excel_file_path, sheet_name='Page 1',
                                      header=None, names=['0', '1', '2', '3'])
    meas_rxlev = dut_signaling[dut_signaling['2'].str.contains(string_to_search, na=False)]
    return list(range(len(meas_rxlev['2'].str.extract('(\d+)').astype(int)))),\
        meas_rxlev['2'].str.extract('(\d+)').astype(int) + variance


def main():

    x_plot, y_plot = get_graph_plot_arrays('DE_C10_CSFB_LC_Signaling export.xlsx', 'RXLEV_FULL_SERVING_CELL', -110)

    fig = plt.figure()
    fig, ax1 = plt.subplots()
    ax1.plot(x_plot, y_plot)
    ax1.set_title('DUT RXLEV 1')
    fig.savefig('dut_gsm_signal_strength.png')
    plt.show()

    x_plot, y_plot = get_graph_plot_arrays('DE_S22_CSFB_LC_Signaling export.xlsx', 'RXLEV_FULL_SERVING_CELL', -110)

    fig = plt.figure()
    fig, ax1 = plt.subplots()
    ax1.plot(x_plot, y_plot)
    ax1.set_title('REF RXLEV 1')
    fig.savefig('ref_gsm_signal_strength.png')
    plt.show()


if __name__ == "__main__":
  main()