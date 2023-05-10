import pandas as pd
from src.settings import data_directory
from src.utilities.parameter_initializer import ParameterInitializer

pd.set_option("display.max_rows", None)


class EpidemiologicalDataPreProcessing:
    """This class creates the epidemiological data to be used for computing the parameters of the epidemiological
    model."""

    def __init__(self, data_paths):
        """This method loads the data for pre-processing.

        :param data_paths:"""

        self.data_paths = data_paths
        self.parameter_initializer = ParameterInitializer(
            data_paths["processed_state_data"]
        )

        self.states = self.parameter_initializer.initialize_state_names()

        self.epidemiological_data = (
            self.parameter_initializer.initialize_epidemiological_model_data()
        )

        # TODO: Look into how significant the difference between state populations is at various points in time in your
        #       data.
        self.state_populations = (
            self.parameter_initializer.initialize_state_populations()
        )

        self.cases_by_vaccination = pd.read_csv(
            f"{data_directory}/old_data/data_by_vaccination_status/booster/cases_by_vaccination_and_booster.csv"
        ).iloc[:395]
        self.deaths_by_vaccination = pd.read_csv(
            f"{data_directory}/old_data/data_by_vaccination_status/booster/deaths_by_vaccination_and_booster.csv"
        ).iloc[:395]
        self.hospitalizations_by_vaccination = pd.read_csv(
            f"{data_directory}/old_data/data_by_vaccination_status/booster/"
            f"hospitalizations_by_vaccination_and_booster.csv"
        ).iloc[:395]

        # self.population = population

    def data_preprocessing(self):
        """This method pre-processes the data for the sub-compartments in the epidemiological model."""

        for state in self.states:
            self.epidemiological_data[state]["date"] = pd.to_datetime(
                self.epidemiological_data[state]["date"]
            )

            self.epidemiological_data[state] = self.epidemiological_data[state].iloc[
                108:503
            ]
            self.epidemiological_data[state].reset_index(inplace=True)

            # Vaccination compartments.
            # self.epidemiological_data[state]["unvaccinated_individuals"] = (
            #     self.state_populations[state]
            #     - self.epidemiological_data[state]["people_vaccinated"]
            # )
            self.epidemiological_data[state]["unvaccinated_individuals"] = (
                self.state_populations[state]
                - self.epidemiological_data[state]["Administered_Dose1_Recip"]
            )

            # self.epidemiological_data[state][
            #     "fully_vaccinated_individuals"
            # ] = self.epidemiological_data[state]["people_fully_vaccinated"]
            self.epidemiological_data[state][
                "fully_vaccinated_individuals"
            ] = self.epidemiological_data[state]["Series_Complete_Yes"]

            # self.epidemiological_data[state][
            #     "boosted_individuals"
            # ] = self.epidemiological_data[state]["total_boosters"]
            self.epidemiological_data[state][
                "boosted_individuals"
            ] = self.epidemiological_data[state]["Additional_Doses"]

            # Computing the vaccination rates.
            self.epidemiological_data[state][
                [
                    "percentage_unvaccinated_to_fully_vaccinated",
                    "percentage_fully_vaccinated_to_boosted",
                ]
            ] = 0

            for i in range(1, len(self.epidemiological_data[state])):
                # Unvaccinated to Fully Vaccinated.
                self.epidemiological_data[state][
                    "percentage_unvaccinated_to_fully_vaccinated"
                ].iloc[i] = (
                    self.epidemiological_data[state]["unvaccinated_individuals"].iloc[
                        i - 1
                    ]
                    - self.epidemiological_data[state]["unvaccinated_individuals"].iloc[
                        i
                    ]
                ) / self.epidemiological_data[
                    state
                ][
                    "unvaccinated_individuals"
                ].iloc[
                    i - 1
                ]

                # Fully Vaccinated to Boosted.
                self.epidemiological_data[state][
                    "percentage_fully_vaccinated_to_boosted"
                ].iloc[i] = (
                    self.epidemiological_data[state]["boosted_individuals"].iloc[i]
                    - self.epidemiological_data[state]["boosted_individuals"].iloc[
                        i - 1
                    ]
                ) / self.epidemiological_data[
                    state
                ][
                    "fully_vaccinated_individuals"
                ].iloc[
                    i - 1
                ]

            # Exposed compartments.
            exposure_multiplier = (
                100 / 0.7
            )  # We have a reference for this. (Cited > 700 times).
            self.epidemiological_data[state]["Exposed"] = (
                self.epidemiological_data[state]["Daily Cases"] * exposure_multiplier
            ).astype(int)

            # Susceptible compartments.
            self.epidemiological_data[state]["Susceptible"] = (
                self.state_populations[state]
                - self.epidemiological_data[state]["Exposed"]
                - self.epidemiological_data[state]["Active Cases"]
                - self.epidemiological_data[state]["Total Recovered"]
                - self.epidemiological_data[state]["Total Deaths (Linear)"]
            )

            # Infected compartments.
            cdc_skew = (
                (
                    self.epidemiological_data[state]["Active Cases"]
                    - self.epidemiological_data[state]["inpatient_beds_used_covid"]
                )
                * (self.cases_by_vaccination["uv_mul"])
            ).astype(int)
            self.epidemiological_data[state]["Infected_UV"] = cdc_skew

            cdc_skew = (
                (
                    self.epidemiological_data[state]["Active Cases"]
                    - self.epidemiological_data[state]["inpatient_beds_used_covid"]
                )
                * (self.cases_by_vaccination["fv_mul"])
            ).astype(int)
            self.epidemiological_data[state]["Infected_FV"] = cdc_skew

            cdc_skew = (
                (
                    self.epidemiological_data[state]["Active Cases"]
                    - self.epidemiological_data[state]["inpatient_beds_used_covid"]
                )
                * (self.cases_by_vaccination["b_mul"])
            ).astype(int)
            self.epidemiological_data[state]["Infected_BV"] = cdc_skew

            # Hospitalized compartments.
            cdc_skew = (
                self.epidemiological_data[state]["inpatient_beds_used_covid"]
                * self.hospitalizations_by_vaccination["uv_mul"]
            ).astype(int)
            self.epidemiological_data[state]["Hospitalized_UV"] = cdc_skew

            cdc_skew = (
                self.epidemiological_data[state]["inpatient_beds_used_covid"]
                * self.hospitalizations_by_vaccination["fv_mul"]
            ).astype(int)
            self.epidemiological_data[state]["Hospitalized_FV"] = cdc_skew

            cdc_skew = (
                self.epidemiological_data[state]["inpatient_beds_used_covid"]
                * self.hospitalizations_by_vaccination["b_mul"]
            ).astype(int)
            self.epidemiological_data[state]["Hospitalized_BV"] = cdc_skew

            # Recovered compartments.
            initial_recovered_unvaccinated_skew = (
                self.epidemiological_data[state]["Total Recovered"].iloc[0]
                * self.cases_by_vaccination["uv_mul"].iloc[0]
            ).astype(int)

            initial_recovered_fully_vaccinated_skew = (
                self.epidemiological_data[state]["Total Recovered"].iloc[0]
                * self.cases_by_vaccination["fv_mul"].iloc[0]
            ).astype(int)

            initial_recovered_booster_vaccinated_skew = (
                self.epidemiological_data[state]["Total Recovered"].iloc[0]
                * self.cases_by_vaccination["b_mul"].iloc[0]
            ).astype(int)

            uv_to_fv = self.epidemiological_data[state][
                "percentage_unvaccinated_to_fully_vaccinated"
            ]
            fv_to_bv = self.epidemiological_data[state][
                "percentage_fully_vaccinated_to_boosted"
            ]

            self.epidemiological_data[state][
                ["Recovered_UV", "Recovered_FV", "Recovered_BV"]
            ] = 0
            self.epidemiological_data[state]["Recovered_UV"].iloc[
                0
            ] = initial_recovered_unvaccinated_skew
            self.epidemiological_data[state]["Recovered_FV"].iloc[
                0
            ] = initial_recovered_fully_vaccinated_skew
            self.epidemiological_data[state]["Recovered_BV"].iloc[
                0
            ] = initial_recovered_booster_vaccinated_skew

            for i in range(1, len(self.epidemiological_data[state])):
                self.epidemiological_data[state]["Recovered_UV"].iloc[i] = (
                    self.epidemiological_data[state]["Recovered_UV"].iloc[i - 1]
                    + self.epidemiological_data[state]["New Recoveries"].iloc[i]
                    * self.cases_by_vaccination["uv_mul"].iloc[i]
                    - uv_to_fv[i]
                    * self.epidemiological_data[state]["Recovered_UV"].iloc[i - 1]
                ).astype(int)
                self.epidemiological_data[state]["Recovered_FV"].iloc[i] = (
                    self.epidemiological_data[state]["Recovered_FV"].iloc[i - 1]
                    + self.epidemiological_data[state]["New Recoveries"].iloc[i]
                    * self.cases_by_vaccination["fv_mul"].iloc[i]
                    + uv_to_fv[i]
                    * self.epidemiological_data[state]["Recovered_UV"].iloc[i - 1]
                    - fv_to_bv[i]
                    * self.epidemiological_data[state]["Recovered_FV"].iloc[i - 1]
                ).astype(int)
                self.epidemiological_data[state]["Recovered_BV"].iloc[i] = (
                    self.epidemiological_data[state]["Recovered_BV"].iloc[i - 1]
                    + self.epidemiological_data[state]["New Recoveries"].iloc[i]
                    * self.cases_by_vaccination["b_mul"].iloc[i]
                    + fv_to_bv[i]
                    * self.epidemiological_data[state]["Recovered_FV"].iloc[i - 1]
                ).astype(int)

            # Deceased compartments.
            initial_deceased_skew = (
                self.epidemiological_data[state]["Total Deaths (Linear)"].iloc[0]
                * self.cases_by_vaccination["uv_mul"].iloc[0]
            ).astype(int)
            cdc_skew = (
                self.epidemiological_data[state]["Daily Deaths"]
                * self.cases_by_vaccination["uv_mul"]
            ).astype(int)
            cdc_skew[0] = 0
            cdc_skew = cdc_skew.cumsum()
            cdc_skew = cdc_skew + initial_deceased_skew
            self.epidemiological_data[state]["Deceased_UV"] = cdc_skew

            initial_deceased_skew = (
                self.epidemiological_data[state]["Total Deaths (Linear)"].iloc[0]
                * self.cases_by_vaccination["fv_mul"].iloc[0]
            ).astype(int)
            cdc_skew = (
                self.epidemiological_data[state]["Daily Deaths"]
                * self.cases_by_vaccination["fv_mul"]
            ).astype(int)
            cdc_skew[0] = 0
            cdc_skew = cdc_skew.cumsum()
            cdc_skew = cdc_skew + initial_deceased_skew
            self.epidemiological_data[state]["Deceased_FV"] = cdc_skew

            initial_deceased_skew = (
                self.epidemiological_data[state]["Total Deaths (Linear)"].iloc[0]
                * self.cases_by_vaccination["b_mul"].iloc[0]
            ).astype(int)
            cdc_skew = (
                self.epidemiological_data[state]["Daily Deaths"]
                * self.cases_by_vaccination["b_mul"]
            ).astype(int)
            cdc_skew[0] = 0
            cdc_skew = cdc_skew.cumsum()
            cdc_skew = cdc_skew + initial_deceased_skew
            self.epidemiological_data[state]["Deceased_BV"] = cdc_skew

            # Accounting for "missing individuals".
            missing_individuals_unvaccinated = self.epidemiological_data[state][
                "unvaccinated_individuals"
            ] - (
                self.epidemiological_data[state]["Infected_UV"]
                + self.epidemiological_data[state]["Hospitalized_UV"]
                + self.epidemiological_data[state]["Recovered_UV"]
                + self.epidemiological_data[state]["Deceased_UV"]
            )

            missing_individuals_fully_vaccinated = self.epidemiological_data[state][
                "fully_vaccinated_individuals"
            ] - (
                self.epidemiological_data[state]["Infected_FV"]
                + self.epidemiological_data[state]["Hospitalized_FV"]
                + self.epidemiological_data[state]["Recovered_FV"]
                + self.epidemiological_data[state]["Deceased_FV"]
            )

            missing_individuals_booster_vaccinated = self.epidemiological_data[state][
                "boosted_individuals"
            ] - (
                self.epidemiological_data[state]["Infected_BV"]
                + self.epidemiological_data[state]["Hospitalized_BV"]
                + self.epidemiological_data[state]["Recovered_BV"]
                + self.epidemiological_data[state]["Deceased_BV"]
            )

            total_missing_individuals_vaccination = (
                missing_individuals_unvaccinated
                + missing_individuals_fully_vaccinated
                + missing_individuals_booster_vaccinated
            )

            self.epidemiological_data[state]["Infected"] = (
                self.epidemiological_data[state]["Infected_UV"]
                + self.epidemiological_data[state]["Infected_FV"]
                + self.epidemiological_data[state]["Infected_BV"]
            )

            self.epidemiological_data[state]["Hospitalized"] = (
                self.epidemiological_data[state]["Hospitalized_UV"]
                + self.epidemiological_data[state]["Hospitalized_FV"]
                + self.epidemiological_data[state]["Hospitalized_BV"]
            )

            self.epidemiological_data[state]["Recovered"] = (
                self.epidemiological_data[state]["Recovered_UV"]
                + self.epidemiological_data[state]["Recovered_FV"]
                + self.epidemiological_data[state]["Recovered_BV"]
            )

            self.epidemiological_data[state]["Deceased"] = (
                self.epidemiological_data[state]["Deceased_UV"]
                + self.epidemiological_data[state]["Deceased_FV"]
                + self.epidemiological_data[state]["Deceased_BV"]
            )

            # Adjusting Susceptible
            self.epidemiological_data[state]["Susceptible_UV"] = (
                self.epidemiological_data[state]["Susceptible"]
                * missing_individuals_unvaccinated
                / total_missing_individuals_vaccination
            ).astype(int)

            self.epidemiological_data[state]["Susceptible_FV"] = (
                self.epidemiological_data[state]["Susceptible"]
                * missing_individuals_fully_vaccinated
                / total_missing_individuals_vaccination
            ).astype(int)

            self.epidemiological_data[state]["Susceptible_BV"] = (
                self.epidemiological_data[state]["Susceptible"]
                * missing_individuals_booster_vaccinated
                / total_missing_individuals_vaccination
            ).astype(int)

            # Adjusting Exposed
            self.epidemiological_data[state]["Exposed_UV"] = (
                self.epidemiological_data[state]["Exposed"]
                * missing_individuals_unvaccinated
                / total_missing_individuals_vaccination
            ).astype(int)

            self.epidemiological_data[state]["Exposed_FV"] = (
                self.epidemiological_data[state]["Exposed"]
                * missing_individuals_fully_vaccinated
                / total_missing_individuals_vaccination
            ).astype(int)

            self.epidemiological_data[state]["Exposed_BV"] = (
                self.epidemiological_data[state]["Exposed"]
                * missing_individuals_booster_vaccinated
                / total_missing_individuals_vaccination
            ).astype(int)

            # Computing the total by vaccination statues across the different compartments.
            self.epidemiological_data[state]["unvaccinated_compartment_total"] = (
                self.epidemiological_data[state]["Susceptible_UV"]
                + self.epidemiological_data[state]["Exposed_UV"]
                + self.epidemiological_data[state]["Infected_UV"]
                + self.epidemiological_data[state]["Hospitalized_UV"]
                + self.epidemiological_data[state]["Recovered_UV"]
                + self.epidemiological_data[state]["Deceased_UV"]
            )

            self.epidemiological_data[state]["fully_vaccinated_compartment_total"] = (
                self.epidemiological_data[state]["Susceptible_FV"]
                + self.epidemiological_data[state]["Exposed_FV"]
                + self.epidemiological_data[state]["Infected_FV"]
                + self.epidemiological_data[state]["Hospitalized_FV"]
                + self.epidemiological_data[state]["Recovered_FV"]
                + self.epidemiological_data[state]["Deceased_FV"]
            )

            self.epidemiological_data[state]["booster_vaccinated_compartment_total"] = (
                self.epidemiological_data[state]["Susceptible_BV"]
                + self.epidemiological_data[state]["Exposed_BV"]
                + self.epidemiological_data[state]["Infected_BV"]
                + self.epidemiological_data[state]["Hospitalized_BV"]
                + self.epidemiological_data[state]["Recovered_BV"]
                + self.epidemiological_data[state]["Deceased_BV"]
            )

            self.epidemiological_data[state]["Original Infected"] = (
                self.epidemiological_data[state]["Active Cases"]
                - self.epidemiological_data[state]["inpatient_beds_used_covid"]
            )

            # Saving the epidemiological model data.
            self.epidemiological_data[state].iloc[:].to_csv(
                f"{data_directory}/epidemiological_model_data/{state}.csv",
                index=False,
                columns=[
                    "date",
                    "unvaccinated_individuals",
                    "fully_vaccinated_individuals",
                    "boosted_individuals",
                    "unvaccinated_compartment_total",
                    "fully_vaccinated_compartment_total",
                    "booster_vaccinated_compartment_total",
                    "percentage_unvaccinated_to_fully_vaccinated",
                    "percentage_fully_vaccinated_to_boosted",
                    "Daily Cases",
                    "Susceptible",
                    "Exposed",
                    "Infected",
                    "Hospitalized",
                    "Recovered",
                    "Deceased",
                    "Original Infected",
                    "inpatient_beds_used_covid",
                    "Total Recovered",
                    "Total Deaths (Linear)",
                    "Susceptible_UV",
                    "Susceptible_FV",
                    "Susceptible_BV",
                    "Exposed_UV",
                    "Exposed_FV",
                    "Exposed_BV",
                    "Infected_UV",
                    "Infected_FV",
                    "Infected_BV",
                    "Hospitalized_UV",
                    "Hospitalized_FV",
                    "Hospitalized_BV",
                    "Recovered_UV",
                    "Recovered_FV",
                    "Recovered_BV",
                    "Deceased_UV",
                    "Deceased_FV",
                    "Deceased_BV",
                ],
            )


data__paths = {
    "processed_state_data": f"{data_directory}/processed_state_data/",
}

epidemiological_data_preprocessing = EpidemiologicalDataPreProcessing(
    data_paths=data__paths
)
epidemiological_data_preprocessing.data_preprocessing()
