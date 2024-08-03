from colorama import Fore, Style, init

# Initialize colorama
init()
company_name = ("                                     *     *    *****     *********     *****    ******     *\n"
                "                                    **     *    *             *         *        *          *\n"
                "                                   ****    *    *****         *         *****    *          ******\n"
                "                                  *    *   *        *         *         *        *          *    *\n"
                "                                 *      *  *    *****         *         *****    ******     *    *\n")

pending = "                                                    S C R I P T - R U N I N G ....."
completed = "\n\n\n                                                    Completed successfully"

capitalized_name = company_name.upper()


def _start_script():
    print(Fore.BLUE + company_name)
    print(Fore.LIGHTGREEN_EX + pending + Style.DIM)


def _end_script():
    print(Fore.LIGHTRED_EX + completed + Style.RESET_ALL)
